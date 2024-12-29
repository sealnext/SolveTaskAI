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

class TicketState(TypedDict):
    """State for the ticket operations subgraph."""
    action: str
    query: str
    ticket_id: str
    
    issue_type_id: Optional[str]
    available_fields: Optional[dict]
    
    result: str

async def process_action(state: TicketState) -> dict:
    """Process the ticket operation and return result."""
    action = state["action"]
    if action not in ["create", "edit", "delete"]:
        state["result"] = f"Error: unknown action: {action}, we only support create, edit, delete"
        return END
    
    return state
    
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
    # Add interrupt at the start to get approval
    state["result"] = f"Ticket deleted with link: https://example.com/ticket/{state['ticket_id']}"
    return state

def create_ticket_graph(checkpointer=None) -> CompiledStateGraph:
    """Create the ticket operations subgraph."""
    builder = StateGraph(TicketState)
    
    builder.add_node("process", process_action)
    builder.add_node("create", create_ticket)
    builder.add_node("edit", edit_ticket)
    builder.add_node("delete", delete_ticket)
    
    builder.add_edge("process", "create")
    builder.add_edge("process", "edit")
    builder.add_edge("process", "delete")
    builder.add_edge("process", END)
    
    builder.set_entry_point("process")
    
    return builder.compile(checkpointer=checkpointer, interrupt_before=["delete"])
