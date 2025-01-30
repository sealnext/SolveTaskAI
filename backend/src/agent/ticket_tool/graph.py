import json
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI
from agent.ticket_tool.utils import (
    extract_json_from_llm_response, 
    validate_field_values,
    format_json_response,
    process_field_update,
)
from agent.ticket_tool.edit_ticket import EditTicketHandler, generate_edit_plan, handle_edit_review
from agent.ticket_tool.create_ticket import CreateTicketHandler
from agent.ticket_tool.delete_ticket import DeleteTicketHandler
from config.logger import auto_log
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from langgraph.graph import StateGraph, END, MessagesState, START
from services.ticketing.client import BaseTicketingClient
import logging
from typing import Dict, Literal, Optional, Tuple, Union
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
    
    issue_type_id: Optional[str] = None
    optional_fields: Optional[dict] = None
    required_fields: Optional[dict] = None

class TicketGraph:
    def __init__(self, ticketing_client: BaseTicketingClient):
        self.client = ticketing_client
        self.create_handler = CreateTicketHandler(ticketing_client)
        self.delete_handler = DeleteTicketHandler(ticketing_client)
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
    async def process_action(self, state: TicketState) -> Union[Command[Literal["create", "generate_edit_plan", "delete", "end"]], dict]:
        """Process the ticket operation and return the next node to execute."""
        is_valid, message = self.validate_and_update_state(state)
        
        if not is_valid:
            state["result"] = message
            return Command(
                update={"result": message},
                goto="end"
            )
        
        action = state.get('action', '')
        if action not in ["create", "edit", "delete"]:
            error_msg = f"Error: unknown action: {action}, we only support create, edit, delete"
            return Command(
                update={"result": error_msg},
                goto="end"
            )
        
        logger.info(f"Action: {state['action']}")
        logger.info(f"Ticket ID: {state['ticket_id']}")
        logger.info(f"Query: {state['detailed_query']}")
        
        # Route based on action and pass the entire state
        state_dict = {
            "action": state["action"],
            "ticket_id": state["ticket_id"],
            "detailed_query": state["detailed_query"],
            "messages": state["messages"]
        }
        
        if action == "edit":
            return Command(
                update=state_dict,
                goto="generate_edit_plan"
            )
        elif action == "create":
            return Command(
                update=state_dict,
                goto="create"
            )
        elif action == "delete":
            return Command(
                update=state_dict,
                goto="delete"
            )
        
        return Command(goto="end")

    async def create_ticket(self, state: TicketState) -> dict:
        """Create a ticket and handle human review process."""
        return await self.create_handler.create_ticket(state)

    async def delete_ticket(self, state: TicketState) -> dict:
        """Delete a ticket and handle human review process."""
        return await self.delete_handler.delete_ticket(state)

    def _create_graph(self) -> CompiledStateGraph:
        """Create the ticket operations subgraph."""
        builder = StateGraph(TicketState)
        
        # Create closures for edit nodes to pass client
        async def _generate_edit_plan_with_client(state: dict) -> Union[Command[Literal["handle_edit_review"]], dict]:
            return await generate_edit_plan(state, client=self.client)
            
        async def _handle_edit_review_with_client(state: dict) -> Union[Command[Literal["handle_edit_review", "end"]], dict]:
            return await handle_edit_review(state, client=self.client)
        
        # Add nodes
        builder.add_node("process", self.process_action)
        builder.add_node("create", self.create_ticket)
        builder.add_node("generate_edit_plan", _generate_edit_plan_with_client)
        builder.add_node("handle_edit_review", _handle_edit_review_with_client)
        builder.add_node("delete", self.delete_ticket)
        
        # Add edges for initial routing
        builder.add_edge(START, "process")
        
        # Add edges to end
        builder.add_edge("create", END)
        builder.add_edge("handle_edit_review", END)
        builder.add_edge("delete", END)
        
        return builder.compile()

    def get_graph(self) -> CompiledStateGraph:
        """Get the compiled graph."""
        return self.graph

# Factory function to create the graph
def create_ticket_graph(ticketing_client: BaseTicketingClient) -> CompiledStateGraph:
    """Create a new ticket graph instance."""
    return TicketGraph(ticketing_client).get_graph()
