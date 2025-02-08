from agent.configuration import AgentConfiguration
from .prompts import EDIT_TICKET_SYSTEM_PROMPT, EDIT_TICKET_USER_PROMPT_TEMPLATE, JSON_EXAMPLE, TICKET_AGENT_PROMPT
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Optional, Literal, Dict, Union, Any, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import FunctionMessage, ToolMessage, AnyMessage, AIMessage, HumanMessage, SystemMessage
from config.logger import auto_log
import logging
from langgraph.prebuilt import ToolNode
from services.ticketing.client import BaseTicketingClient
from langgraph.types import interrupt, Command
from langgraph.prebuilt import InjectedState
from langchain_core.tools.base import InjectedToolCallId
from typing import Sequence
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from enum import Enum
from langgraph.errors import GraphInterrupt
from langgraph.graph import add_messages
from langchain_core.callbacks import dispatch_custom_event
import json
import re
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    action: Literal["edit", "create", "delete"] = Field(description="The action to perform on the ticket")
    detailed_query: str = Field(description="Detailed description of what needs to be done")
    ticket_id: str = Field(description="The ID of the ticket to operate on")

class TicketAgentState(BaseModel):
    """State for the ticket agent."""
    messages: Annotated[Sequence[AnyMessage], add_messages]
    internal_messages: Annotated[Sequence[AnyMessage], add_messages]

    review_config: Optional[Dict[str, Any]] = None
    needs_review: bool = False
    done: bool = False

class ReviewAction(str, Enum):
    """Available review actions based on operation type."""
    # Common actions
    CONFIRM = "confirm"  # Proceed with operation as is
    CANCEL = "cancel"      # Cancel the entire operation

    # Edit specific
    UPDATE_FIELDS = "update_fields"     # Update specific fields
    MODIFY_CHANGES = "modify_changes"   # Modify the proposed changes

    # Create specific
    ADJUST_TEMPLATE = "adjust_template" # Adjust the ticket template
    MODIFY_DETAILS = "modify_details"   # Modify ticket details

    # Delete specific
    ARCHIVE_INSTEAD = "archive_instead" # Archive instead of delete
    SOFT_DELETE = "soft_delete"        # Soft delete option

class OperationDetails(TypedDict):
    """Details specific to the operation type."""
    field_updates: Optional[dict[str, Any]]  # For JIRA field mappings
    changes_description: str                 # Human readable changes
    api_mappings: Optional[dict[str, Any]]   # Future JIRA API mappings

class ReviewConfig(TypedDict):
    """Enhanced review configuration."""
    question: str                    # Review prompt
    operation_type: Literal["create", "edit", "delete"] # Operation type
    available_actions: list[ReviewAction]  # Actions available for this operation
    expected_payload_schema: dict       # Reference to Pydantic model schema
    preview_data: dict                  # Preview data for review
    metadata: Optional[dict[str, Any]] # Additional metadata

class JiraTicketUpdate(BaseModel):
    """Pydantic model for Jira ticket update."""
    fields: dict[str, Any]
    update: dict[str, Any]

def clean_json_response(raw_response: str) -> dict:
    """
    Extract and clean JSON content from LLM response containing:
    - <json_output> tags
    - Potential code comments
    - Extra text outside JSON

    Example input:
    Here's the suggested update:
    <json_output>
    {
        // This is a comment
        "update": {
            "priority": "High" /* inline comment */
        },
        "validation": {...}
    }
    </json_output>
    Please review carefully.
    """
    # Extract content between <json_output> tags
    json_matches = re.findall(r'<json_output>(.*?)</json_output>', raw_response, re.DOTALL)
    if not json_matches:
        raise ValueError("No valid JSON output found in response")

    # Take the last JSON block if multiple present
    json_content = json_matches[-1].strip()

    # Remove line comments and inline comments
    cleaned = '\n'.join([
        line.split('//')[0].split('#')[0].strip()
        for line in json_content.split('\n')
        if not line.strip().startswith('//')
    ])
    # Remove /* */ comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Remove trailing commas
    cleaned = re.sub(r',\s*}', '}', cleaned)
    cleaned = re.sub(r',\s*]', ']', cleaned)

    return json.loads(cleaned)

def create_ticket_agent(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    client: BaseTicketingClient = None
) -> StateGraph:
    """Create a new ticket agent graph instance."""

    if client is None:
        raise ValueError("Ticketing client is required")

    @tool(args_schema=TicketToolInput)
    @auto_log("ticket_agent.create_ticket")
    async def create_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        config: RunnableConfig,
    ) -> ToolMessage:
        """Tool for creating tickets."""
        dispatch_custom_event(
            "agent_progress",
            {
                "message": f"Creating new ticket {ticket_id}...",
                "ticket_id": ticket_id
            },
            config=config
        )
        tool_call_id = config.get("tool_call_id")
        return ToolMessage(content="Ticket created successfully", tool_call_id=tool_call_id)

    async def handle_review_process(
        review_config: ReviewConfig,
    ) -> str:
        """Simplified review handler with direct confirmation flow."""
        try:
            # Get final payload from review response
            review_response = interrupt({
                "question": review_config.get("question", ""),
                "preview": review_config.get("preview_data", {}),
                "expected_schema": review_config.get("expected_payload_schema", {}),
                "available_actions": review_config.get("available_actions", []),
                "metadata": review_config.get("metadata", {})
            })

            match review_response["action"]:
                case ReviewAction.CONFIRM:
                    return await _handle_direct_confirmation(
                        review_response["payload"],
                        review_response["ticket"]
                    )

                case ReviewAction.CANCEL:
                    return "Operation cancelled by user"

                case _:
                    raise ValueError(f"Unsupported action: {review_response["action"]}")

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            logger.error(f"Review process failed: {str(e)}", exc_info=True)
            return f"Review process error: {str(e)}"

    @auto_log("ticket_agent.edit_ticket")
    async def edit_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[TicketAgentState, InjectedState],
        config: RunnableConfig,
    ) -> Command:
        """Tool for editing JIRA tickets."""
        try:
            is_resuming = config.get("configurable")['__pregel_resuming']

            if is_resuming:
                message = await handle_review_process({})

                tool_message = ToolMessage(
                            content=message,
                            tool_call_id=tool_call_id)

                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [tool_message],
                        "done": True
                        }
                    )

            # --- Initial Execution Path ---
            # Notify about starting the process
            dispatch_custom_event(
                "agent_progress",
                {"message": f"Mapping changes for ticket {ticket_id}...", "ticket_id": ticket_id},
                config=config
            )

            # Get metadata and current values
            metadata = await client.get_ticket_edit_issue_metadata(ticket_id)
            available_fields = {
                k: {sk: sv for sk, sv in v.items() if sv not in (None, {})}
                for k, v in metadata['fields'].items()
            }
            current_values = await client.get_ticket_fields(ticket_id, list(available_fields.keys()))

            # Add current values to metadata
            for field_key in available_fields:
                available_fields[field_key]['current_value'] = current_values.get(field_key)

            # Generate edit plan with LLM
            agent_config = AgentConfiguration()
            llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature)

            response = await llm.ainvoke([{
                "role": "system",
                "content": EDIT_TICKET_SYSTEM_PROMPT
            }, {
                "role": "user",
                "content": EDIT_TICKET_USER_PROMPT_TEMPLATE.format(
                    detailed_query=detailed_query,
                    available_fields=available_fields,
                    json_example=JSON_EXAMPLE
                )
            }])

            # Process and validate response
            field_updates = clean_json_response(response.content)
            if not isinstance(field_updates, dict) or "update" not in field_updates or "validation" not in field_updates:
                raise ValueError("Invalid LLM response structure")

            # Handle unknown fields and update description
            unknown_fields = [
                field for section in ['fields', 'update']
                for field in field_updates.get(section, {})
                if field not in available_fields
            ]

            # Process unknown fields if any...
            if unknown_fields:
                # Extract values from unknown fields and append to description only if description exists
                description_additions = []
                for field in unknown_fields:
                    field_value = field_updates.get('fields', {}).get(field) or field_updates.get('update', {}).get(field)
                    if field_value:
                        description_additions.append(f"{field}: {json.dumps(field_value, indent=2)}")

                # Only append to description if it exists in field_updates
                if description_additions:
                    description_exists = False
                    current_description = ""

                    # Check if description is being set in fields
                    if 'fields' in field_updates and 'description' in field_updates['fields']:
                        description_exists = True
                        current_description = field_updates['fields']['description']
                    # Check if description is being set in update
                    elif 'update' in field_updates and 'description' in field_updates['update']:
                        description_exists = True
                        for update in field_updates['update']['description']:
                            if 'set' in update:
                                current_description = update['set']
                                break

                    # Only modify description if it exists in updates
                    if description_exists:
                        new_content = "\n\n".join([
                            current_description,
                            "Additional context from unmapped fields:",
                            *description_additions
                        ]).strip()

                        # Update in the same section where it was found
                        if 'fields' in field_updates and 'description' in field_updates['fields']:
                            field_updates['fields']['description'] = new_content
                        elif 'update' in field_updates and 'description' in field_updates['update']:
                            field_updates['update']['description'] = [
                                {"set": new_content}
                            ]

                        # Add validation entries only for modified description
                        if 'validation' not in field_updates:
                            field_updates['validation'] = {}

                        field_updates['validation']['description'] = {
                            "confidence": "Medium",
                            "validation": "Modified to include unmapped fields"
                        }

                # Clean unknown fields from both sections
                for section in ['fields', 'update']:
                    if section in field_updates:
                        field_updates[section] = {
                            k: v for k, v in field_updates[section].items()
                            if k in available_fields
                        }

            # Prepare review configuration
            review_config = ReviewConfig(
                question=f"Confirm changes for ticket {ticket_id}:",
                operation_type="edit",
                available_actions=[ReviewAction.CONFIRM, ReviewAction.CANCEL],  # Simplified actions
                expected_payload_schema=JiraTicketUpdate.schema(),  # Reference to Pydantic model schema
                preview_data=field_updates,
                metadata={"ticket_id": ticket_id}
            )
            message = await handle_review_process(
                review_config
            )

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            logger.error(f"Edit ticket error: {str(e)}")
            return ToolMessage(
                content=f"Error processing edit request: {str(e)}",
                tool_call_id=tool_call_id,
                name="edit_ticket"
            )

    @tool(args_schema=TicketToolInput)
    @auto_log("ticket_agent.delete_ticket")
    async def delete_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        config: RunnableConfig,
    ) -> ToolMessage:
        """Tool for deleting tickets."""
        dispatch_custom_event(
            "agent_progress",
            {
                "message": f"Deleting ticket {ticket_id}...",
                "ticket_id": ticket_id
            },
            config=config
        )
        tool_call_id = config.get("tool_call_id")
        return ToolMessage(content="Ticket deleted successfully", tool_call_id=tool_call_id)

    @tool
    async def search_jira_entity(
        entity_type: Literal["account", "sprint", "issue"],
        value: str
    ) -> str:
        """
        Search for a Jira entity by specified criteria.

        Parameters:
        - entity_type: account, sprint, issue, epic, project
        - value: the value to search for
        """
        try:
            match entity_type:
                case "account":
                    result = await client.search_user(value)
                    total = result.get("total", 0)
                    users = result.get("users", [])

                    if total == 1:
                        return f"Success! Use this accountId instead of the username: {users[0]['accountId']}"
                    elif total > 1:
                        user_list = "\n".join([
                            f"- {user['displayName']}: {user['accountId']}"
                            for user in users
                        ])
                        return (
                            "There are multiple accounts that may match the name, "
                            "please use only the accountId for the most relevant name:\n"
                            f"{user_list}"
                        )
                    else:
                        return f"No accounts found matching '{value}'. Please verify the username and try again."
                case "sprint":
                    result = await client.find_sprint_by_name(
                        sprint_name=value
                    )
                case "issue":
                    result = await client.search_issue_by_name(
                        issue_name=value,
                        max_results=5
                    )
                    total = result.get("total", 0)
                    issues = result.get("issues", [])

                    if total == 1:
                        issue = issues[0]
                        return f"Success! Use this issue reference - Key: {issue['key']}"
                    elif total > 1:
                        issue_list = "\n".join([
                            f"- {issue['fields']['summary']}\n  Key: {issue['key']}"
                            for issue in issues
                        ])
                        return (
                            "Multiple matching issues found. Please use the most relevant Key:\n"
                            f"{issue_list}"
                        )
                    else:
                        return f"No issues found matching '{value}'. Please verify the issue name and try again."
                case _:
                    raise ValueError(f"Unsupported entity type: {entity_type}")
            result = f"Successfully found entity, please use the id from the response instead of the raw names: {result}"

            return result

        except Exception as e:
            return f"Search failed: {e}"

    builder = StateGraph(TicketAgentState)

    prep_tools = ToolNode(
        tools=[create_ticket, edit_ticket, delete_ticket, search_jira_entity],
        messages_key="internal_messages"
    )

    async def call_model_with_tools(state: TicketAgentState, config: RunnableConfig):
        """Node that calls the LLM with internal message history."""
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        llm_with_tools = llm.bind_tools([create_ticket, edit_ticket, delete_ticket, search_jira_entity])

        if state.done:
            return {"messages": [ToolMessage(content=state.internal_messages[-1].content, tool_call_id=state.messages[-1].tool_calls[-1]['id'])]}

        if not state.internal_messages and state.messages[-1].tool_calls:
            args = state.messages[-1].tool_calls[0]['args']

            # Format the ticket_id section
            ticket_id_section = f"- Ticket ID: {args['ticket_id']}" if args.get('ticket_id') else ''

            # Create the structured prompt using the template
            structured_prompt = TICKET_AGENT_PROMPT.format(
                action=args.get('action', 'Not specified'),
                query=args.get('detailed_query', 'Not specified'),
                ticket_id_section=ticket_id_section
            )

            if not state.internal_messages:
                state.internal_messages = [SystemMessage(content=structured_prompt)]
            else:
                # Append the new message while keeping the history
                state.internal_messages.append(SystemMessage(content=structured_prompt))

        response = await llm_with_tools.ainvoke(state.internal_messages)
        state.internal_messages.append(response)

        if len(response.tool_calls) > 0:
            return Command(goto="tools", update={"internal_messages": state.internal_messages})

        return {"messages": [ToolMessage(content=response.content, tool_call_id=state.messages[-1].tool_calls[0]["id"])]}

    async def _handle_direct_confirmation(
        jira_payload: Dict[str, Any],
        ticket_id: str,
    ) -> str:
        """Validate and apply direct confirmation payload to Jira."""
        try:
            await client.update_ticket(
                ticket_id=ticket_id,
                payload=jira_payload,
                notify_users=False
            )

            fields_changed = ", ".join(jira_payload.get('fields', {}).keys())
            updates_made = ", ".join(jira_payload.get('update', {}).keys())
            
            changes_list = []
            if fields_changed:
                changes_list.append(f"fields: {fields_changed}")
            if updates_made:
                changes_list.append(f"updates: {updates_made}")
                
            return "Successfully updated Jira ticket " + ticket_id + ". Please let the user know we changed ONLY the following fields: " + "; ".join(changes_list)

        except ValidationError as e:
            logger.error(f"Invalid Jira payload: {e.errors()}")
            return f"Invalid request format: {e}"
        except Exception as e:
            logger.error(f"Jira update failed: {str(e)}")
            return f"Jira update error: {str(e)}"

    builder.add_node("agent", call_model_with_tools)
    builder.add_node("tools", prep_tools)
    # builder.add_node("handle_review", handle_review)

    builder.set_entry_point("agent")
    builder.add_edge(START, "agent")
    builder.add_edge("tools", "agent")

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph


