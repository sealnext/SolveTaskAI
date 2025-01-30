import json
import asyncio
import logging
from typing import Dict, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt, Command
from langgraph.errors import GraphInterrupt
from agent.configuration import AgentConfiguration
from agent.ticket_tool.utils import (
    extract_json_from_llm_response,
    validate_field_values,
    format_json_response,
    process_field_update,
)
from services.ticketing.client import BaseTicketingClient

logger = logging.getLogger(__name__)

RETRY_DELAY_SECONDS = 1
RETRY_TIMEOUT_SECONDS = 5
MAX_RETRIES = 3

class FieldMapping(BaseModel):
    value: str = Field(description="The exact value to set for the field")
    confidence: Literal["High", "Medium", "Low"] = Field(description="Confidence level in the mapping")
    validation: Literal["Valid", "Needs Validation"] = Field(description="Whether the value needs user validation")

class TicketFieldMapping(BaseModel):
    mapped_fields: Dict[str, FieldMapping] = Field(
        description="Dictionary mapping Jira field names to their corresponding values, confidence levels, and validation status"
    )

class EditTicketHandler:
    def __init__(self, ticketing_client: BaseTicketingClient):
        self.client = ticketing_client

    async def safe_edit_ticket(self, ticket_id: str, fields: dict) -> tuple[int, str]:
        """Helper to safely edit a ticket and return status code and message."""
        try:
            status_code = await self.client.edit_ticket(ticket_id, fields)
            if status_code == 204:
                logger.info(f"Successfully updated ticket {ticket_id}")
                return status_code, f"Successfully updated ticket {ticket_id}"
            else:
                logger.warning(f"Unexpected status code {status_code} when updating ticket {ticket_id}")
                return status_code, f"Unexpected status code {status_code} when updating ticket {ticket_id}"
        except Exception as e:
            error_msg = f"Failed to update ticket {ticket_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return 500, error_msg

    async def _generate_edit_plan(self, state: dict) -> dict:
        """Internal method to generate edit plan."""
        try:
            # Get Jira field metadata
            metadata = await self.client.get_ticket_edit_issue_metadata(state['ticket_id'])
            available_fields = {}
            for field_key, field_info in metadata['fields'].items():
                field_dict = field_info.copy()  # Start with a copy of all field info
                
                # Remove any None values or empty dicts
                field_dict = {k: v for k, v in field_dict.items() if v is not None and v != {}}
                
                if field_dict:  # Only add if we have any fields
                    available_fields[field_key] = field_dict

            # Get current values for fields we might want to update
            fields_to_fetch = list(available_fields.keys())
            current_values = await self.client.get_ticket_fields(state['ticket_id'], fields_to_fetch)

            # Add current values to the available_fields info
            for field_key, field_info in available_fields.items():
                field_info['current_value'] = current_values.get(field_key)

        except Exception as e:
            logger.error(f"Failed to get Jira metadata: {e}", exc_info=True)
            raise ValueError(f"Could not get Jira field metadata: {str(e)}")

        # Base system prompt
        system_prompt = """You are an AI Jira Field Mapping Specialist. Your task is to accurately map user requests to Jira fields, ensuring all parts of the request are addressed efficiently and correctly."""

        # Add error context if this is a retry after LLM mapping failed
        if 'last_error' in state:
            system_prompt += f"\n\nPrevious attempt failed with error: {state['last_error']}\nPlease adjust your mapping accordingly."
            logger.info(f"Retrying LLM mapping with error context: {state['last_error']}")

        json_example = """{
        "update": {
            "summary": [
            {"set": "new title"}
            ],
            "assignee": [
            {"set": {"accountId": "example_id_account"}}
            ],
            "labels": [
            {"add": "security"}
            ],
            "customfield_10020": [
            {"set": 1} 
            ],
            "description": [
            {"set": "new description"}
            ],
            "issuelinks": [
            {
                "add": {
                "type": {"name": "Relates"},
                "inwardIssue": {"key": "PZ-5"}
                }
            }
            ]
        },
        "validation": {
          "summary": {"confidence": "High", "validation": "Valid"},
          "assignee": {"confidence": "High", "validation": "Valid"},
          "labels": {"confidence": "High", "validation": "Valid"},
          "customfield_10020": {"confidence": "Low", "validation": "Needs Validation"},
          "description": {"confidence": "High", "validation": "Valid"},
          "priority": {"confidence": "High", "validation": "Valid"},
          "issuelinks": {"confidence": "Medium", "validation": "Valid"}
        }
        }
        """
        
        user_prompt = f"""First, analyze the following user request:

        <user_request>
        {state['detailed_query']}
        </user_request>

        Now, review the available Jira fields with their schema, allowed operations, and current values:

        <jira_fields>
        {available_fields}
        </jira_fields>

        ### Instructions:

        1. Analyze the user's request and extract all elements that need to be updated.

        2. For each element:
           - Identify the correct Jira field by matching it with the `name` or `customfield_ID` from `jira_fields`.
           - Don't invent new fields, only map to existing ones in jira_fields. 
           - Compare with the field's current value to determine if an update is needed.
           - Verify the requested operation (e.g., `add`, `set`, `remove`) is allowed for that field.
           - Ensure the value format aligns with the field's `type` and `schema`.

        3. Create a **`validation`** section for each field:
           - IMPORTANT: Every field in the update section MUST have a corresponding entry in the validation section
           - Use "Needs Validation" status whenever there's uncertainty about IDs, references, or exact values
           - Set appropriate confidence levels (High, Medium, Low)
           - Missing validation info for any field in the update section will cause an error

        4. Structure your output as JSON in the following format, only return the raw json:

        Disclaimer, this is just an simple example. You need to make you're own json based on the jira_fields and user_request.
        </json_example>
        {json_example}
        </json_example>

        ### Key Notes:
        - Compare your proposed changes with the current values to ensure meaningful updates.
        - Derive the correct structure and format dynamically based on the `schema` and `operations` in `jira_fields`.
        - Use the **`update`** section for all dynamic changes and the **`validation`** section for confidence and validation information.
        - CRITICAL: Every field in the update section MUST have a corresponding entry in the validation section
        - If unsure about a mapping, use a lower confidence level and mark it for validation, don't add comments.
        - If some fields cannot be mapped, add them to the description as text.
        - Instead of adding comments related to placeholder values, just use "Needs Validation" on validation field. Keep the placeholder only.
        - Due to recent GDPR changes, referencing user fields (such as reporter, assignee) now require the property id to be set with a user's account ID rather than using name
        - NEVER PUT COMMENTS IN JSON, ONLY RETURN THE JSON WITH NO EXPLANATIONS
        - Dont invent new fields, only map to existing ones in jira_fields. If it's not possible to map, add it to the description as text.
        
        Proceed with your analysis and provide only the JSON output."""
        # Get LLM response
        agent_config = AgentConfiguration()
        llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature, model_kwargs={'response_format': {"type": "json_object"}})
        response = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        try:
            # Parse and validate LLM response
            json_content = extract_json_from_llm_response(response.content)
            field_updates = json.loads(json_content)
            
            # Basic validation
            validate_field_values(field_updates)
            
            # Validate fields exist in Jira
            unknown_fields = [
                field for field in field_updates['update']
                if field not in available_fields
            ]
            
            if unknown_fields:
                raise ValueError(f"Unknown Jira fields: {', '.join(unknown_fields)}")
            
            # Store the field updates and available fields in state for the review handler
            state['field_updates'] = field_updates
            state['available_fields'] = available_fields
            
            return state

        except Exception as e:
            error_msg = f"Error processing LLM response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state['last_error'] = error_msg
            raise ValueError(error_msg)

    async def _handle_review(self, state: dict) -> dict:
        """Internal method to handle review."""
        try:
            field_updates = state['field_updates']
            available_fields = state['available_fields']
            
            # If we don't have a review action yet, we need to ask for review
            if 'review_action' not in state:
                # Setup for human review
                last_message = state['messages'][-1]
                tool_call = last_message.tool_calls[0]
                tool_call_id = tool_call['id']
                
                # Present changes for review
                human_review = interrupt({
                    "question": f"Review changes for ticket {state['ticket_id']}:",
                    "tool_call": tool_call,
                    "tool_call_id": tool_call_id,
                    "details": field_updates,
                    "available_actions": {
                        "continue": {
                            "description": "Apply these changes as they are",
                            "request_format": {"action": "continue"}
                        },
                        "update": {
                            "description": "Update specific field values",
                            "request_format": {
                                "action": "update",
                                "data": {"field_updates": {"field_name": "new value"}}
                            }
                        },
                        "remap": {
                            "description": "Remap fields to different Jira fields",
                            "request_format": {
                                "action": "remap",
                                "data": {"field_mappings": {"current_field": "new_jira_field"}}
                            }
                        },
                        "cancel": {
                            "description": "Cancel the edit operation",
                            "request_format": {"action": "cancel"}
                        }
                    }
                })
                
                # Store the review action in state
                state['review_action'] = human_review
            
            # Process the review action
            human_review = state['review_action']
            try:
                match human_review["action"]:
                    case "continue":
                        return await self._handle_continue_action(state, field_updates)
                    case "update":
                        return await self._handle_update_action(state, field_updates, human_review)
                    case "remap":
                        return await self._handle_remap_action(state, field_updates, human_review, available_fields)
                    case "cancel":
                        state['result'] = "Edit operation cancelled"
                        return state
                    case _:
                        raise ValueError(f"Invalid action: {human_review['action']}")

            except Exception as e:
                logger.error(f"Error in {human_review['action']} action: {e}", exc_info=True)
                raise ValueError(f"Error in {human_review['action']} action: {str(e)}")

        except GraphInterrupt as i:
            # Re-raise interrupts to be handled by the message generator
            raise i
        except Exception as e:
            error_msg = f"Error handling review: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state['last_error'] = error_msg
            raise ValueError(error_msg)

    async def _handle_continue_action(self, state: dict, ticket_changes: TicketFieldMapping) -> dict:
        """Handle the continue action with retries."""
        retry_count = 0

        # Check for fields needing validation
        invalid_fields = [
            field for field, data in ticket_changes.mapped_fields.items()
            if data.validation == "Needs Validation"
        ]
        if invalid_fields:
            raise ValueError(f"Fields need validation: {', '.join(invalid_fields)}")
        
        # Send only values to Jira
        jira_updates = {
            field: data.value 
            for field, data in ticket_changes.mapped_fields.items()
        }

        while retry_count < MAX_RETRIES:
            try:
                async with asyncio.timeout(RETRY_TIMEOUT_SECONDS):
                    status_code, message = await self.safe_edit_ticket(state['ticket_id'], jira_updates)
                
                if status_code == 204:
                    return_message = f"{message}\n\nApplied changes:\n{format_json_response(ticket_changes.model_dump())}"
                    state['result'] = return_message
                    return state
                
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Retry {retry_count}/{MAX_RETRIES} after error: {message}")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {message}")
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Timeout on retry {retry_count}/{MAX_RETRIES}")
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts due to timeout")
            except Exception as e:
                retry_count += 1
                logger.error(f"Error on retry {retry_count}/{MAX_RETRIES}: {str(e)}", exc_info=True)
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {str(e)}")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    async def _handle_update_action(self, state: dict, ticket_changes: TicketFieldMapping, human_review: dict) -> dict:
        """Handle the update action with retries."""
        retry_count = 0

        if "data" not in human_review or "field_updates" not in human_review["data"]:
            raise ValueError("Missing field updates data")
        
        field_updates = human_review["data"]["field_updates"]
        if not field_updates:
            raise ValueError("No fields to update")
        
        # Process updates
        results = []
        for field_name, new_value in field_updates.items():
            if field_name not in ticket_changes.mapped_fields:
                results.append(f"❌ {field_name}: Field not found")
                continue
                
            result_message, str_value = process_field_update(field_name, new_value)
            if str_value:
                ticket_changes.mapped_fields[field_name].value = str_value
                ticket_changes.mapped_fields[field_name].validation = "Valid"
            results.append(result_message)
        
        if not any(r.startswith("✅") for r in results):
            raise ValueError("No fields were updated successfully")
        
        # Send only values to Jira
        jira_updates = {
            field: data.value 
            for field, data in ticket_changes.mapped_fields.items()
        }

        while retry_count < MAX_RETRIES:
            try:
                async with asyncio.timeout(RETRY_TIMEOUT_SECONDS):
                    status_code, message = await self.safe_edit_ticket(state['ticket_id'], jira_updates)
                
                if status_code == 204:
                    return_message = f"{message}\n\nResults:\n" + "\n".join(results)
                    state['result'] = return_message
                    return state
                
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Retry {retry_count}/{MAX_RETRIES} after error: {message}")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {message}")
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Timeout on retry {retry_count}/{MAX_RETRIES}")
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts due to timeout")
            except Exception as e:
                retry_count += 1
                logger.error(f"Error on retry {retry_count}/{MAX_RETRIES}: {str(e)}", exc_info=True)
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {str(e)}")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    async def _handle_remap_action(self, state: dict, ticket_changes: TicketFieldMapping, human_review: dict, available_fields: dict) -> dict:
        """Handle the remap action with retries."""
        retry_count = 0

        if "data" not in human_review or "field_mappings" not in human_review["data"]:
            raise ValueError("Missing field mappings data")
        
        field_mappings = human_review["data"]["field_mappings"]
        if not field_mappings:
            raise ValueError("No fields to remap")
        
        # Validate target fields
        unknown_targets = [
            field for field in field_mappings.values() 
            if field not in available_fields
        ]
        if unknown_targets:
            raise ValueError(f"Unknown target fields in Jira: {', '.join(unknown_targets)}")
        
        # Process remapping
        remapped = {}
        results = []
        
        # Keep unchanged fields
        for field, data in ticket_changes.mapped_fields.items():
            if field not in field_mappings:
                remapped[field] = data
        
        # Process remapped fields
        for old_field, new_field in field_mappings.items():
            if old_field not in ticket_changes.mapped_fields:
                results.append(f"❌ {old_field}: Source field not found")
                continue
            
            remapped[new_field] = ticket_changes.mapped_fields[old_field]
            results.append(f"✅ {old_field} -> {new_field}")
        
        if not any(r.startswith("✅") for r in results):
            raise ValueError("No fields were remapped successfully")
        
        # Update our model
        ticket_changes.mapped_fields = remapped
        
        # Send only values to Jira
        jira_updates = {
            field: data.value 
            for field, data in ticket_changes.mapped_fields.items()
        }

        while retry_count < MAX_RETRIES:
            try:
                async with asyncio.timeout(RETRY_TIMEOUT_SECONDS):
                    status_code, message = await self.safe_edit_ticket(state['ticket_id'], jira_updates)
                
                if status_code == 204:
                    return_message = f"{message}\n\nResults:\n" + "\n".join(results)
                    state['result'] = return_message
                    return state
                
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Retry {retry_count}/{MAX_RETRIES} after error: {message}")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {message}")
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Timeout on retry {retry_count}/{MAX_RETRIES}")
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts due to timeout")
            except Exception as e:
                retry_count += 1
                logger.error(f"Error on retry {retry_count}/{MAX_RETRIES}: {str(e)}", exc_info=True)
                if retry_count >= MAX_RETRIES:
                    raise ValueError(f"Failed to update ticket after {MAX_RETRIES} attempts. Last error: {str(e)}")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

# Graph nodes
async def generate_edit_plan(state: dict, *, client: BaseTicketingClient) -> Union[Command[Literal["handle_edit_review"]], dict]:
    """Node for generating edit plan."""
    handler = EditTicketHandler(client)
    result = await handler._generate_edit_plan(state)
    return Command(
        update=result,
        goto="handle_edit_review"
    )

async def handle_edit_review(state: dict, *, client: BaseTicketingClient) -> Union[Command[Literal["handle_edit_review", "end"]], dict]:
    """Node for handling edit review."""
    try:
        handler = EditTicketHandler(client)
        result = await handler._handle_review(state)
        # If we have a result, we're done
        if "result" in result:
            return Command(
                update=result,
                goto="end"
            )
        # Otherwise, we need to continue reviewing
        return Command(
            update=result,
            goto="handle_edit_review"
        )
    except Exception as e:
        return Command(
            update={"result": str(e)},
            goto="end"
        ) 