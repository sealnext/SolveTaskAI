import operator
from typing import TypedDict
from langgraph.graph import START, StateGraph
from langchain_core.messages import FunctionMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import END
from typing import Optional
from langgraph.types import interrupt
from typing import Annotated
from langgraph.graph import StateGraph, END, START, MessagesState
from typing import Literal
import logging
from langchain_core.messages import ToolMessage, HumanMessage
from typing import Tuple, Dict, Any
from dataclasses import fields
from dataclasses import dataclass
from langgraph.graph import MessagesState

logger = logging.getLogger(__name__)

class TicketState(MessagesState):
    """State for the ticket operations subgraph."""
    action: str
    detailed_query: str
    ticket_id: str
    
    issue_type_id: Optional[str] = None
    available_fields: Optional[dict] = None
    
    result: str = ""

def validate_and_update_state(state: TicketState) -> Tuple[bool, str]:
    """
    Validates the incoming tool call arguments against TicketState fields and updates state if valid.
    """
    # Get the last message and extract tool calls
    last_message = state.get('messages', [])[-1]
    
    if not hasattr(last_message, 'additional_kwargs'):
        return False, "Message has no additional_kwargs"
        
    tool_call = last_message.tool_calls[-1]
    if not tool_call:
        return False, "No tool calls found in the message"

    args = tool_call.get('args', {})

    # Get fields directly from TicketState
    ticket_state_fields = [
        "action",
        "ticket_id",
        "detailed_query",
        "issue_type_id",
        "available_fields"
    ]

    for field in ticket_state_fields:
        if field in args:
            value = args[field]
            state[field] = value

    if not (state.get('action') and state.get('ticket_id')):
        return False, "Missing required fields: action and ticket_id"
    
    return True, "State updated successfully"

async def process_action(state: TicketState) -> dict:
    """Process the ticket operation and return the next node to execute."""
    is_valid, message = validate_and_update_state(state)
    
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
    
    return {"action":action}

async def create_ticket(state: TicketState) -> dict:
    """Create a ticket and return the result."""
    state["result"] = f"Ticket created with link: https://example.com/ticket/{state['ticket_id']}"
    return state

async def edit_ticket(state: TicketState) -> dict:
    """Edit a ticket and return the result."""
    state["result"] = f"Ticket edited with link: https://example.com/ticket/{state['ticket_id']}"
    return state

async def delete_ticket(state: TicketState) -> dict:
    """Delete a ticket and return the result."""
    logger.info(f"Deleting ticket: {state['ticket_id']}")
    logger.info(f"State: {state}")
    logger.info(f"Messages: {state.get('messages', [])}")
    
    # Get the tool_call_id from the last AI message
    last_message = state['messages'][-1]
    tool_call = last_message.additional_kwargs['tool_calls'][0]
    tool_call_id = tool_call.get('id')
    
    logger.info(f"Tool call ID: {tool_call_id}")
    
    # Add result to state
    result = f"Ticket {state['ticket_id']} was successfully deleted. You can no longer access it at: https://example.com/ticket/{state['ticket_id']}"
    
    return {
        "messages": [
            ToolMessage(
                content=result,
                tool_call_id=tool_call_id,
                name="ticket_tool"
            )
        ]
    }

def route_action(state: TicketState) -> str:
    """Route the action with logging."""
    action = state.get("action")
    logger.info(f"Routing action to: {action}")
    return action

def create_ticket_graph() -> CompiledStateGraph:
    """Create the ticket operations subgraph."""
    builder = StateGraph(TicketState)
    
    builder.add_node("process", process_action)
    builder.add_node("create", create_ticket)
    builder.add_node("edit", edit_ticket)
    builder.add_node("delete", delete_ticket)
    
    # Add conditional edges based on the action
    builder.add_conditional_edges(
        "process",
        route_action,
        {
            "create": "create",
            "edit": "edit",
            "delete": "delete",
            "end": END
        }
    )
    
    # Add edges from operations to END
    builder.add_edge("create", END)
    builder.add_edge("edit", END)
    # builder.add_edge("delete", END)
    
    builder.set_entry_point("process")
    
    # Return compiled graph with interrupt before delete
    return builder.compile(interrupt_before=["delete"])
