from config.logger import auto_log
from langgraph.graph.state import CompiledStateGraph
from typing import Optional
from langgraph.types import interrupt
from langgraph.graph import StateGraph, END
import logging
from langchain_core.messages import ToolMessage
from typing import Tuple
from langgraph.graph import MessagesState
from services.ticketing.client import BaseTicketingClient

logger = logging.getLogger(__name__)

class TicketState(MessagesState):
    """State for the ticket operations subgraph."""
    action: str
    detailed_query: str
    ticket_id: str
    
    issue_type_id: Optional[str]
    available_fields: Optional[dict]
    result: str

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

    async def edit_ticket(self, state: TicketState) -> dict:
        """Edit a ticket and return the result."""
        # TODO: Implement real ticket editing using self.client
        state["result"] = f"Ticket edited with link: https://example.com/ticket/{state['ticket_id']}"
        return state

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
