from agent.configuration import AgentConfiguration
from .prompts import EDIT_TICKET_SYSTEM_PROMPT, EDIT_TICKET_USER_PROMPT_TEMPLATE, JSON_EXAMPLE
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Optional, Literal, Dict, Union, Any, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import FunctionMessage, ToolMessage, AnyMessage, AIMessage, HumanMessage
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

logger = logging.getLogger(__name__)

class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    action: Literal["edit", "create", "delete"] = Field(description="The action to perform on the ticket")
    detailed_query: str = Field(description="Detailed description of what needs to be done")
    ticket_id: str = Field(description="The ID of the ticket to operate on")

class TicketAgentState(BaseModel):
    """State for the ticket agent."""
    messages: Sequence[AnyMessage]
    action: Optional[str] = None
    ticket_id: Optional[str] = None
    detailed_query: Optional[str] = None
    original_tool_call: Optional[Dict[str, Any]] = None
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

def create_ticket_agent(checkpointer: Optional[AsyncPostgresSaver] = None, client: BaseTicketingClient = None) -> StateGraph:
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
        """Tool for editing tickets."""
        
        # 1. Get JIRA metadata and current values
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

        # 2. Use LLM to generate edit plan
        agent_config = AgentConfiguration()
        llm = ChatOpenAI(
            model=agent_config.model, 
            temperature=agent_config.temperature,
            model_kwargs={'response_format': {"type": "json_object"}}
        )
        
        response = await llm.ainvoke([
            {"role": "system", "content": EDIT_TICKET_SYSTEM_PROMPT},
            {"role": "user", "content": EDIT_TICKET_USER_PROMPT_TEMPLATE.format(
                detailed_query=detailed_query,
                available_fields=available_fields,
                json_example=JSON_EXAMPLE
            )}
        ])

        # 3. Parse and validate LLM response
        try:
            field_updates = json.loads(response.content)
            
            # Basic validation
            if not isinstance(field_updates, dict):
                raise ValueError("LLM response is not a dictionary")
            if "update" not in field_updates or "validation" not in field_updates:
                raise ValueError("Missing required sections in LLM response")
            
            # Validate fields exist in JIRA
            unknown_fields = [
                field for field in field_updates['update']
                if field not in available_fields
            ]
            if unknown_fields:
                raise ValueError(f"Unknown Jira fields: {', '.join(unknown_fields)}")
            
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            raise ValueError(f"Failed to process field updates: {str(e)}")

        # 4. Setup review config
        review_config = {
            "question": f"Review changes for ticket {ticket_id}:",
            "tool_call": state.original_tool_call,
            "tool_call_id": state.original_tool_call['id'],
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
                "api_mappings": available_fields
            },
            "metadata": {
                "ticket_id": ticket_id,
                "original_description": detailed_query,
            }
        }

        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="Review required for ticket changes",
                        tool_call_id=tool_call_id,
                        name="edit_ticket"
                    )
                ],
                "review_config": review_config,
                "needs_review": True
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
    
    builder = StateGraph(TicketAgentState)
    
    prep_tools = ToolNode([create_ticket, edit_ticket, delete_ticket])

    async def call_model_with_tools(state: TicketAgentState, config: RunnableConfig):
        """Node that calls the LLM with the current state."""
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Find the original tool call and keep only the last 2 relevant messages
        original_tool_call = None
        for i, message in enumerate(reversed(state.messages)):
            if (isinstance(message, AIMessage) and 
                hasattr(message, 'tool_calls') and 
                message.tool_calls and 
                message.tool_calls[0]['name'] == 'ticket_tool'):
                original_tool_call = message.tool_calls[0]
                # Keep only the human message and the tool call message
                human_message = state.messages[len(state.messages) - 2 - i]  # Get the human message before tool call
                state.messages = [human_message, message]
                break

        if not original_tool_call:
            logger.warning("No original tool call found")
            return {"messages": state.messages}

        # Extract information from the original tool call
        args = original_tool_call['args']
        action = args['action']
        ticket_id = args['ticket_id']
        detailed_query = args['detailed_query']

        # Create a single concatenated message
        context_message = f"""Original request: {human_message.content}

Ticket Details:
- Ticket ID: {ticket_id}
- Action: {action}
- Changes Requested: {detailed_query}"""

        initial_system_message = f"""You are a ticket management assistant handling the '{action}' operation for ticket {ticket_id}.
First handle any necessary sub-operations for this ticket."""
        
        final_instruction = f"""Now that you've handled the sub-operations, you must use the {action}_ticket tool 
to complete the main operation. Include all relevant information from your previous actions in the detailed_query parameter.

Remember to use these exact parameters:
- action: "{action}"
- ticket_id: "{ticket_id}"
- detailed_query: <your detailed summary>"""

        # Combine all into a single system message
        combined_system_message = f"""{initial_system_message}

{context_message}

{final_instruction}"""

        messages = [{
            "role": "system",
            "content": combined_system_message
        }]

        llm_with_tools = llm.bind_tools([create_ticket, edit_ticket, delete_ticket])
        response = await llm_with_tools.ainvoke(messages)
        
        return {
            "messages": [response],
            "original_tool_call": original_tool_call
        }

    async def format_final_response(state: TicketAgentState) -> Dict[str, Any]:
        """Final node that formats the response using the original tool call."""
        if not state.original_tool_call:
            logger.warning("No original tool call found in state")
            return {"messages": []}

        # Just pass through the last message
        return {"messages": state.messages}

    def should_continue(state: TicketAgentState) -> Literal["tools", "format_response", "handle_review", "__end__"]:
        """Enhanced flow control for subgraph operations."""
        if not state.messages:
            return "__end__"
        
        last_msg = state.messages[-1]
        
        # Check state for review flag instead of message metadata
        if state.needs_review:
            return "handle_review"
        
        if isinstance(last_msg, ToolMessage):
            if last_msg.tool_call_id and last_msg.tool_call_id.startswith(f"{state.action}_tool_"):
                return "format_response"
            return "tools"
        
        # Continue if there are pending tool calls
        if hasattr(last_msg, "tool_calls") and len(last_msg.tool_calls) > 0:
            return "tools"
        
        return "__end__"

    async def handle_review(state: Annotated[TicketAgentState, InjectedState]) -> Dict[str, Any]:
        """Review handler node that manages the review process and processes the response."""
        try:
            if not state.review_config:
                logger.error("No review_config found in state or last message")
                raise ValueError("No review configuration available")
            
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
                        return {
                            "messages": [
                                ToolMessage(
                                    content="Edit operation cancelled",
                                    tool_call_id=review_config["tool_call_id"]
                                )
                            ]
                        }
                    case _:
                        raise ValueError(f"Invalid action: {human_review['action']}")

            except Exception as e:
                logger.error(f"Error in {human_review['action']} action: {e}", exc_info=True)
                raise ValueError(f"Error in {human_review['action']} action: {str(e)}")

        except GraphInterrupt as i:
            # Re-raise interrupts to be handled by the graph
            raise i
        except Exception as e:
            error_msg = f"Error handling review: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)

    async def _handle_continue_action(state: TicketAgentState, details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the continue action from review."""
        final_message = ToolMessage(
            content=f"Changes applied successfully on JIRA",
            tool_call_id=state.original_tool_call["id"]
        )
        
        return {
            "messages": [final_message],  # Just return the final message
            "needs_review": False
        }

    async def _handle_update_fields_action(
        state: TicketAgentState, 
        details: Dict[str, Any], 
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the update_fields action from review."""
        field_updates = review.get("data", {}).get("field_updates", {})
        # Update the changes with new field values
        updated_changes = {**details["changes_description"], **field_updates}
        
        return {
            "messages": [
                ToolMessage(
                    content=f"Updated changes for ticket {details['ticket_id']}: {updated_changes}",
                    tool_call_id=state.review_config["tool_call_id"]
                )
            ]
        }

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

    # Add nodes
    builder.add_node("agent", call_model_with_tools)
    builder.add_node("tools", prep_tools)
    builder.add_node("format_response", format_final_response)
    builder.add_node("handle_review", handle_review)

    # Add edges - direct path through review
    builder.set_entry_point("agent")
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue)
    builder.add_edge("tools", "handle_review")  # Always go to review first
    builder.add_edge("handle_review", "format_response")  # After review, go back to agent
    builder.add_edge("format_response", END)

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph


