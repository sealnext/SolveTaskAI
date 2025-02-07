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
    
    action: Optional[str] = None
    ticket_id: Optional[str] = None
    detailed_query: Optional[str] = None
    review_config: Optional[Dict[str, Any]] = None
    needs_review: bool = False

class ReviewAction(str, Enum):
    """Available review actions based on operation type."""
    # Common actions
    CONTINUE = "continue"  # Proceed with operation as is
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
    tool_call: dict[str, Any]       # Original tool call
    tool_call_id: str               # Tool call ID
    operation_type: Literal["create", "edit", "delete"] # Operation type
    available_actions: list[ReviewAction]  # Actions available for this operation
    details: OperationDetails       # Operation specific details
    metadata: Optional[dict[str, Any]] # Additional metadata

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
            # Notify about starting the process
            dispatch_custom_event(
                "agent_progress",
                {
                    "message": f"Mapping requested changes for ticket {ticket_id}...",
                    "ticket_id": ticket_id
                },
                config=config
            )

            # Get JIRA metadata and current values
            metadata = await client.get_ticket_edit_issue_metadata(ticket_id)
            available_fields = {}
            for field_key, field_info in metadata['fields'].items():
                field_dict = field_info.copy()
                field_dict = {k: v for k, v in field_dict.items() if v is not None and v != {}}
                if field_dict:
                    available_fields[field_key] = field_dict

            current_values = await client.get_ticket_fields(ticket_id, list(available_fields.keys()))
            
            # Add current values to metadata
            for field_key in available_fields:
                available_fields[field_key]['current_value'] = current_values.get(field_key)

            # Use LLM to generate edit plan
            agent_config = AgentConfiguration()
            llm = ChatOpenAI(
                model=agent_config.model, 
                temperature=agent_config.temperature
            )
            
            response = await llm.ainvoke([
                {"role": "system", "content": EDIT_TICKET_SYSTEM_PROMPT},
                {"role": "user", "content": EDIT_TICKET_USER_PROMPT_TEMPLATE.format(
                    detailed_query=detailed_query,
                    available_fields=available_fields,
                    json_example=JSON_EXAMPLE
                )}
            ])

            # Parse and validate LLM response
            try:
                field_updates = clean_json_response(response.content)
                
                # Basic validation
                if not isinstance(field_updates, dict):
                    raise ValueError("LLM response is not a dictionary")
                if "update" not in field_updates or "validation" not in field_updates:
                    raise ValueError("Missing required sections in LLM response")
                
                # Check for unknown fields
                unknown_fields = []
                
                # Check fields section
                if "fields" in field_updates:
                    unknown_fields.extend([
                        field for field in field_updates['fields']
                        if field not in available_fields
                    ])
                
                # Check update section
                if "update" in field_updates:
                    unknown_fields.extend([
                        field for field in field_updates['update']
                        if field not in available_fields
                    ])
                
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
                
                # Setup review config
                review_config = {
                    "question": f"Review changes for ticket {ticket_id}:",
                    "tool_call": state.messages[-1].tool_calls[0],
                    "tool_call_id": tool_call_id,  # Use injected tool_call_id
                    "operation_type": "edit",
                    "available_actions": [
                        ReviewAction.CONTINUE,
                        ReviewAction.UPDATE_FIELDS,
                        ReviewAction.MODIFY_CHANGES,
                        ReviewAction.CANCEL
                    ],
                    "details": {
                        "changes_description": detailed_query,
                        "field_updates": field_updates,
                        "api_mappings": available_fields,
                        "metadata": {
                            "ticket_id": ticket_id,
                            "original_description": detailed_query,
                        }
                    }
                }

                return Command(
                    goto="handle_review",
                    update={
                        "review_config": review_config,
                        "needs_review": True
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing LLM response: {str(e)}")
                return Command(
                    update={
                        "internal_messages": [
                            ToolMessage(
                                content=f"Failed to process field updates: {str(e)}",
                                tool_call_id=tool_call_id,
                                name="edit_ticket"
                            )
                        ]
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in edit_ticket: {str(e)}")
            return Command(
                update={
                    "internal_messages": [
                        ToolMessage(
                            content=f"Error processing edit request: {str(e)}",
                            tool_call_id=tool_call_id,
                            name="edit_ticket"
                        )
                    ]
                }
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

        if state.needs_review:
            return Command(goto="handle_review", update={"internal_messages": state.internal_messages})

        response = await llm_with_tools.ainvoke(state.internal_messages)
        state.internal_messages.append(response)

        if len(response.tool_calls) > 0:
            return Command(goto="tools", update={"internal_messages": state.internal_messages})
        
        return {"messages": [ToolMessage(content=response.content, tool_call_id=state.messages[-1].tool_calls[0]["id"])]}
        
    async def handle_review(state: Annotated[TicketAgentState, InjectedState]) -> Command | dict[str, Any]:
        """Review handler node that manages the review process and processes the response."""
        try:
            if not state.review_config:
                logger.error("No review_config found in state or last message")
                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                content="Error: No review configuration available",
                                tool_call_id=state.messages[-1].tool_calls[0]["id"]
                            )
                        ]
                    }
                )
            
            review_config = state.review_config
            # Define available actions with their formats
            available_actions = {
                ReviewAction.CONTINUE: {
                    "description": "Apply these changes as they are",
                    "request_format": {"action": "continue"}
                },
                ReviewAction.UPDATE_FIELDS: {
                    "description": "Update specific field values",
                    "request_format": {
                        "action": "update_fields",
                        "data": {"field_updates": {"field_name": "new value"}}
                    }
                },
                ReviewAction.MODIFY_CHANGES: {
                    "description": "Modify the proposed changes",
                    "request_format": {
                        "action": "modify_changes",
                        "data": {"changes_description": "new changes in human readable format"}
                    }
                },
                ReviewAction.CANCEL: {
                    "description": "Cancel the operation",
                    "request_format": {"action": "cancel"}
                }
            }

            # Get human review input
            human_review = interrupt({
                "question": review_config["question"],
                "tool_call": review_config["tool_call"],
                "tool_call_id": review_config["tool_call_id"],
                "details": review_config["details"],
                "available_actions": available_actions
            })

            # Process the review action
            try:
                match human_review["action"]:
                    case "continue":
                        return await _handle_continue_action(state, review_config["details"])
                    case "update_fields":
                        return await _handle_update_fields_action(state, review_config["details"], human_review)
                    case "modify_changes":
                        return await _handle_modify_changes_action(state, review_config["details"], human_review)
                    case "cancel":
                        return Command(
                            update={
                                "messages": [
                                    ToolMessage(
                                        content="Edit operation cancelled",
                                        tool_call_id=review_config["tool_call_id"]
                                    )
                                ]
                            }
                        )
                    case _:
                        return Command(
                            update={
                                "messages": [
                                    ToolMessage(
                                        content=f"Invalid action: {human_review['action']}",
                                        tool_call_id=review_config["tool_call_id"]
                                    )
                                ]
                            }
                        )

            except Exception as e:
                logger.error(f"Error in {human_review['action']} action: {e}", exc_info=True)
                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                content=f"Error in {human_review['action']} action: {str(e)}",
                                tool_call_id=review_config["tool_call_id"]
                            )
                        ]
                    }
                )

        except GraphInterrupt as i:
            # Re-raise interrupts to be handled by the graph
            raise i
        except Exception as e:
            error_msg = f"Error handling review: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=error_msg,
                            tool_call_id=state.messages[-1].tool_calls[0]["id"]
                        )
                    ]
                }
            )

    async def _handle_continue_action(state: TicketAgentState, details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the continue action - apply changes directly to Jira."""
        try:
            # Create payload with only fields and update sections
            jira_payload = {
                'fields': details['field_updates'].get('fields', {}),
                'update': details['field_updates'].get('update', {})
            }
            
            # Get ticket ID from metadata
            ticket_id = details['metadata']['ticket_id']
            
            # Call update_ticket with notify_users=False to prevent spam
            await client.update_ticket(
                ticket_id=ticket_id,
                payload=jira_payload,
                notify_users=False
            )
            
            return {
                "messages": [
                    ToolMessage(
                        content="Changes applied successfully to Jira",
                        tool_call_id=state.review_config["tool_call_id"]
                    )
                ],
                "needs_review": False
            }
        except Exception as e:
            logger.error(f"Failed to apply changes to Jira: {e}")
            raise ValueError(f"Failed to apply changes to Jira: {str(e)}")

    async def _handle_update_fields_action(
        state: TicketAgentState, 
        details: Dict[str, Any], 
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle updating specific field values."""
        try:
            # Get the new field updates from review
            new_field_updates = review.get("data", {}).get("field_updates", {})
            
            # Update the original field_updates with new values
            original_updates = details['field_updates']
            
            # Update fields section
            if 'fields' in new_field_updates:
                if 'fields' not in original_updates:
                    original_updates['fields'] = {}
                original_updates['fields'].update(new_field_updates['fields'])
                
            # Update update section
            if 'update' in new_field_updates:
                if 'update' not in original_updates:
                    original_updates['update'] = {}
                original_updates['update'].update(new_field_updates['update'])
            
            # Return to review with updated fields
            return {
                "messages": [
                    ToolMessage(
                        content="Fields updated. Please review the changes.",
                        tool_call_id=state.review_config["tool_call_id"]
                    )
                ],
                "review_config": {
                    **state.review_config,
                    "details": {
                        **details,
                        "field_updates": original_updates
                    }
                },
                "needs_review": True
            }
        except Exception as e:
            logger.error(f"Failed to update fields: {e}")
            raise ValueError(f"Failed to update fields: {str(e)}")

    async def _handle_modify_changes_action(
        state: TicketAgentState, 
        details: Dict[str, Any], 
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the modify_changes action from review."""
        changes_description = review.get("data", {}).get("changes_description", "")
        # Modify the changes description
        modified_changes = f"{changes_description} (modified)"
        
        return {
            "messages": [
                ToolMessage(
                    content=f"Modified changes for ticket {details['ticket_id']}: {modified_changes}",
                    tool_call_id=state.review_config["tool_call_id"]
                )
            ]
        }

    builder.add_node("agent", call_model_with_tools)
    builder.add_node("tools", prep_tools)
    builder.add_node("handle_review", handle_review)

    builder.set_entry_point("agent")
    builder.add_edge(START, "agent")
    builder.add_edge("tools", "agent")
    builder.add_edge("handle_review", "agent")

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph


