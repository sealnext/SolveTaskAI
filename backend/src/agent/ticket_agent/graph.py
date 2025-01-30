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
from typing import Sequence
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from enum import Enum
from langgraph.errors import GraphInterrupt
from langgraph.graph import add_messages

logger = logging.getLogger(__name__)

class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    action: Literal["edit", "create", "delete"] = Field(description="The action to perform on the ticket")
    detailed_query: str = Field(description="Detailed description of what needs to be done")
    ticket_id: str = Field(description="The ID of the ticket to operate on")

class TicketAgentState(BaseModel):
    """State for the ticket agent."""
    messages: Annotated[Sequence[AnyMessage], add_messages] = []
    action: Optional[str] = None
    ticket_id: Optional[str] = None
    detailed_query: Optional[str] = None
    original_tool_call: Optional[Dict[str, Any]] = None
    review_config: Optional[Dict[str, Any]] = None

class ReviewAction(str, Enum):
    CONTINUE = "continue"
    UPDATE = "update"
    REMAP = "remap"
    CANCEL = "cancel"

class ReviewConfig(TypedDict):
    """Configuration for review process."""
    question: str
    tool_call: Dict[str, Any]
    tool_call_id: str
    details: Dict[str, Any]

def create_ticket_agent(checkpointer: Optional[AsyncPostgresSaver] = None) -> StateGraph:
    """Create a new ticket agent graph instance."""
    
    @tool(args_schema=TicketToolInput)
    @auto_log("ticket_agent.create_ticket")
    async def create_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        config: RunnableConfig,
    ) -> ToolMessage:
        """Tool for creating tickets."""
        tool_call_id = config.get("tool_call_id")
        return ToolMessage(content="Ticket created successfully", tool_call_id=tool_call_id)

    @auto_log("ticket_agent.edit_ticket")
    async def edit_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        state: Annotated[TicketAgentState, InjectedState],
    ) -> Dict[str, Any]:
        """Tool for editing tickets."""
        
        last_message = state.messages[-1]
        current_tool_call = last_message.tool_calls[0]

        # Configure the review as a plain dict
        review_config = {
            "question": f"Review changes for ticket {ticket_id}:",
            "tool_call": state.original_tool_call,
            "tool_call_id": state.original_tool_call['id'],
            "details": {
                "ticket_id": ticket_id,
                "changes": detailed_query
            }
        }
        
        # Create a ToolMessage with the review configuration
        tool_message = ToolMessage(
            content="Review required for ticket changes",
            tool_call_id=current_tool_call['id'],
            name="edit_ticket",
            additional_kwargs={
                "review_required": True,
                "review_config": review_config
            }
        )
        
        return {
            "messages": [tool_message],
            "review_config": review_config
        }

    @tool(args_schema=TicketToolInput)
    @auto_log("ticket_agent.delete_ticket")
    async def delete_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        config: RunnableConfig,
    ) -> ToolMessage:
        """Tool for deleting tickets."""
        tool_call_id = config.get("tool_call_id")
        message = ToolMessage(content="Ticket deleted successfully", tool_call_id=tool_call_id)
        return {"messages": [message]}
    
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
            return {"messages": state.messages}

        # Create a ToolMessage that responds to the original tool call
        final_message = ToolMessage(
            content=f"Successfully completed {state.action} operation for ticket {state.ticket_id}",
            tool_call_id=state.original_tool_call["id"]
        )

        return {"messages": [final_message]}

    def should_continue(state: TicketAgentState) -> Literal["tools", "format_response", "handle_review", "__end__"]:
        """Enhanced flow control for subgraph operations."""
        if not state.messages:
            return "__end__"
        
        last_msg = state.messages[-1]
        
        # Check for review required in ToolMessage
        if isinstance(last_msg, ToolMessage):
            if last_msg.additional_kwargs.get("review_required"):
                return "handle_review"
            
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
            # Get review_config from the last message if not in state
            if not state.review_config:
                last_message = state.messages[-1]
                if isinstance(last_message, ToolMessage):
                    state.review_config = last_message.additional_kwargs.get("review_config")
            
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
                ReviewAction.UPDATE: {
                    "description": "Update specific field values",
                    "request_format": {
                        "action": "update",
                        "data": {"field_updates": {"field_name": "new value"}}
                    }
                },
                ReviewAction.REMAP: {
                    "description": "Remap fields to different ticket fields",
                    "request_format": {
                        "action": "remap",
                        "data": {"field_mappings": {"current_field": "new_ticket_field"}}
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
                    case "update":
                        return await _handle_update_action(state, review_config["details"], human_review)
                    case "remap":
                        return await _handle_remap_action(state, review_config["details"], human_review)
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
        return {
            "messages": [
                ToolMessage(
                    content=f"Proceeding with changes for ticket {details['ticket_id']}",
                    tool_call_id=state.review_config["tool_call_id"]
                )
            ]
        }

    async def _handle_update_action(
        state: TicketAgentState, 
        details: Dict[str, Any], 
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the update action from review."""
        field_updates = review.get("data", {}).get("field_updates", {})
        # Update the changes with new field values
        updated_changes = {**details["changes"], **field_updates}
        
        return {
            "messages": [
                ToolMessage(
                    content=f"Updated changes for ticket {details['ticket_id']}: {updated_changes}",
                    tool_call_id=state.review_config["tool_call_id"]
                )
            ]
        }

    async def _handle_remap_action(
        state: TicketAgentState, 
        details: Dict[str, Any], 
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the remap action from review."""
        field_mappings = review.get("data", {}).get("field_mappings", {})
        # Apply field remapping
        remapped_changes = {
            field_mappings.get(k, k): v 
            for k, v in details["changes"].items()
        }
        
        return {
            "messages": [
                ToolMessage(
                    content=f"Remapped changes for ticket {details['ticket_id']}: {remapped_changes}",
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
    builder.add_edge("handle_review", "agent")  # After review, go back to agent
    builder.add_edge("format_response", END)

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph


