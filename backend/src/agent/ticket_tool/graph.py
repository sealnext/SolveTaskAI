from config.logger import auto_log
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from langgraph.graph import StateGraph, END, MessagesState
import asyncio
from services.ticketing.client import BaseTicketingClient
import logging
from typing import Dict, Literal, Optional, Tuple
from pydantic import BaseModel, Field

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

class TicketState(MessagesState):
    """State for the ticket operations subgraph."""
    action: str
    detailed_query: str
    ticket_id: str
    
    issue_type_id: Optional[str]
    optional_fields: Optional[dict]
    required_fields: Optional[dict]

class TicketGraph:
    def __init__(self, ticketing_client: BaseTicketingClient):
        self.client = ticketing_client
        self.graph = self._create_graph()
    
    def validate_and_update_state(self, state: TicketState) -> Tuple[bool, str]:
        """Validates the incoming tool call arguments against TicketState fields and updates state if valid."""
        last_message = state.get('messages', [])[-1]
        
        if not hasattr(last_message, 'additional_kwargs'):
            return False, "Message has no additional_kwargs"
            
        tool_call = last_message.tool_calls[-1]
        if not tool_call:
            return False, "No tool calls found in the message"

        args = tool_call.get('args', {})
        ticket_state_fields = ["action", "ticket_id", "detailed_query", "issue_type_id", "available_fields"]

        for field in ticket_state_fields:
            if field in args:
                state[field] = args[field]

        if not (state.get('action') and state.get('ticket_id')):
            return False, "Missing required fields: action and ticket_id"
        
        return True, "State updated successfully"

    @auto_log("agent.ticket_tool.process_action")
    async def process_action(self, state: TicketState) -> dict:
        """Process the ticket operation and return the next node to execute."""
        is_valid, message = self.validate_and_update_state(state)
        
        if not is_valid:
            state["result"] = message
            return {"action": "end"}
        
        action = state.get('action', '')
        if action not in ["create", "edit", "delete"]:
            state["result"] = f"Error: unknown action: {action}, we only support create, edit, delete"
            return {"action": "end"}
        
        logger.info(f"Action: {state['action']}")
        logger.info(f"Ticket ID: {state['ticket_id']}")
        logger.info(f"Query: {state['detailed_query']}")
        
        return state

    async def create_ticket(self, state: TicketState) -> dict:
        """Create a ticket and return the result."""
        # TODO: Implement real ticket creation using self.client
        state["result"] = f"Ticket created with link: https://example.com/ticket/{state['ticket_id']}"
        return state

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

    async def edit_ticket(self, state: TicketState) -> dict:
        """Edit a ticket and handle human review process."""
        try:
            # Get Jira field metadata
            metadata = await self.client.get_ticket_edit_issue_metadata(state['ticket_id'])
            available_fields = {}
            for field_key, field_info in metadata.items():
                field_dict = {}
                
                if name := field_info.get('name'):
                    field_dict['name'] = name
                    
                if schema := field_info.get('schema', {}):
                    if type_ := schema.get('type'):
                        field_dict['type'] = type_
                    if schema != {}:
                        field_dict['schema'] = schema
                    if allowed_values := schema.get('allowedValues'):
                        field_dict['allowedValues'] = allowed_values
                        
                if operations := field_info.get('operations'):
                    field_dict['operations'] = operations
                
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
            {"set": "Implement user authentication feature"}
            ],
            "assignee": [
            {"set": {"accountId": "712020:a823bbba-4892-467e-b134-c994bd109f94"}}
            ],
            "labels": [
            {"add": "security"}
            ],
            "customfield_10020": [
            {"set": 1} 
            ],
            "description": [
            {"set": "This feature is critical for the upcoming release."}
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
           - Compare with the field's current value to determine if an update is needed.
           - Verify the requested operation (e.g., `add`, `set`, `remove`) is allowed for that field.
           - Ensure the value format aligns with the field's `type` and `schema`:
             - For `array` fields, use `add` or `remove` for single items, and `set` for replacing the entire array.
             - For `user` fields, use `set` with an object containing the `name` or `accountId`.
             - For `string` fields, use `set` with a plain string value.

        3. Create a **`validation`** section for each field:
           - Include `"confidence"` to indicate how certain the mapping is (`High`, `Medium`, `Low`).
           - Include `"validation"` to indicate whether the field's value is valid or requires further review (`Valid`, `Needs Validation`).

        4. Structure your output as JSON in the following format:

        {json_example}

        ### Key Notes:
        - Compare your proposed changes with the current values to ensure meaningful updates.
        - Derive the correct structure and format dynamically based on the `schema` and `operations` in `jira_fields`.
        - Use the **`update`** section for all dynamic changes and the **`validation`** section for confidence and validation information.
        - If unsure about a mapping, use a lower confidence level and mark it for validation.

        Proceed with your analysis and provide the JSON output."""
        # Get LLM response
        agent_config = AgentConfiguration()
        llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature)
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
            normalize_field_values(field_updates)
            
            # Validate fields exist in Jira
            unknown_fields = [
                field for field in field_updates 
                if field not in available_fields
            ]
            if unknown_fields:
                raise ValueError(f"Unknown Jira fields: {', '.join(unknown_fields)}")
            
            # Convert to Pydantic model
            ticket_changes = TicketFieldMapping(
                mapped_fields={
                    field_name: FieldMapping(**field_data)
                    for field_name, field_data in field_updates.items()
                }
            )

            # Setup for human review
            last_message = state['messages'][-1]
            tool_call = last_message.tool_calls[0]
            tool_call_id = tool_call['id']

            # Present changes for review
            human_review = interrupt({
                "question": f"Review changes for ticket {state['ticket_id']}:",
                "tool_call": tool_call,
                "details": ticket_changes.model_dump(),
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

            try:
                # Verify ticket still exists
                if not await self.client.ticket_exists(state['ticket_id']):
                    raise ValueError(f"Ticket {state['ticket_id']} no longer exists")

                match human_review["action"]:
                    case "continue":
                        return await self._handle_continue_action(state, ticket_changes)
                    case "update":
                        return await self._handle_update_action(state, ticket_changes, human_review)
                    case "remap":
                        return await self._handle_remap_action(state, ticket_changes, human_review, available_fields)
                    case "cancel":
                        state['result'] = "Edit operation cancelled"
                        return state
                    case _:
                        raise ValueError(f"Invalid action: {human_review['action']}")

            except Exception as e:
                logger.error(f"Error in {human_review['action']} action: {e}", exc_info=True)
                raise ValueError(f"Error in {human_review['action']} action: {str(e)}")

        except Exception as e:
            error_msg = f"Error processing LLM response: {str(e)}"
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

    async def delete_ticket(self, state: TicketState) -> dict:
        """Delete a ticket and handle human review process."""
        last_message = state['messages'][-1]
        tool_call = last_message.tool_calls[0]
        tool_call_id = tool_call['id']
        
        human_review = interrupt({
            "question": f"Please review deletion of ticket {state['ticket_id']}:",
            "tool_call": tool_call,
            "available_actions": {
                "update": {
                    "description": "Update the ticket ID",
                    "request_format": {
                        "action": "update",
                        "data": {
                            "ticket_id": "new-ticket-id"
                        }
                    }
                },
                "feedback": {
                    "description": "Provide manual feedback on the ticket operation",
                    "request_format": {
                        "action": "feedback",
                        "data": {
                            "feedback": "your feedback message"
                        }
                    }
                },
                "continue": {
                    "description": "Continue with the current operation",
                    "request_format": {
                        "action": "continue"
                    }
                }
            }
        })

        try:
            match human_review["action"]:
                case "update":
                    new_ticket_id = human_review["data"]["ticket_id"]
                    await self.client.delete_ticket(new_ticket_id)
                    return_message = f"Successfully deleted ticket {new_ticket_id}"
                case "feedback":
                    return_message = f"Operation cancelled. Feedback: {human_review['data']['feedback']}"
                case "continue":
                    await self.client.delete_ticket(state['ticket_id'])
                    return_message = f"Successfully deleted ticket {state['ticket_id']}"
                case _:
                    return_message = "Invalid action"

        except Exception as e:
            return_message = f"Failed to delete ticket: {str(e)}"

        return {
            "messages": [
                ToolMessage(
                    content=return_message,
                    tool_call_id=tool_call_id,
                    name="ticket_tool"
                )
            ]
        }

    def route_action(self, state: TicketState) -> str:
        """Route the action with logging."""
        action = state.get("action")
        logger.info(f"Routing action to: {action}")
        return action

    def _create_graph(self) -> CompiledStateGraph:
        """Create the ticket operations subgraph."""
        builder = StateGraph(TicketState)
        
        builder.add_node("process", self.process_action)
        builder.add_node("create", self.create_ticket)
        builder.add_node("edit", self.edit_ticket)
        builder.add_node("delete", self.delete_ticket)
        
        builder.add_conditional_edges(
            "process",
            self.route_action,
            {
                "create": "create",
                "edit": "edit",
                "delete": "delete",
                "end": END
            }
        )
        
        builder.add_edge("create", END)
        builder.add_edge("edit", END)
        builder.add_edge("delete", END)
        
        builder.set_entry_point("process")
        
        return builder.compile()

    def get_graph(self) -> CompiledStateGraph:
        """Get the compiled graph."""
        return self.graph

# Factory function to create the graph
def create_ticket_graph(ticketing_client: BaseTicketingClient) -> CompiledStateGraph:
    """Create a new ticket graph instance."""
    return TicketGraph(ticketing_client).get_graph()
