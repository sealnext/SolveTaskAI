import logging
from typing import Dict, Optional
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from services.ticketing.client import BaseTicketingClient

logger = logging.getLogger(__name__)

class DeleteTicketHandler:
    def __init__(self, ticketing_client: BaseTicketingClient):
        self.client = ticketing_client

    async def delete_ticket(self, state: dict) -> dict:
        """Delete a ticket and handle human review process."""
        try:
            # Get ticket details for confirmation
            ticket_details = await self.client.get_ticket_fields(state['ticket_id'], ['summary', 'description', 'status'])
            
            # Setup for human review
            last_message = state['messages'][-1]
            tool_call = last_message.tool_calls[0]
            tool_call_id = tool_call['id']
            
            # Present ticket details for confirmation
            human_review = interrupt({
                "question": f"Please review deletion of ticket {state['ticket_id']}:",
                "tool_call": tool_call,
                "tool_call_id": tool_call_id,
                "details": ticket_details,
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
                        # Verify the new ticket exists
                        await self.client.get_ticket_fields(new_ticket_id, ['id'])
                        await self.client.delete_ticket(new_ticket_id)
                        return_message = f"Successfully deleted ticket {new_ticket_id}"
                    case "feedback":
                        return_message = f"Operation cancelled. Feedback: {human_review['data']['feedback']}"
                    case "continue":
                        await self.client.delete_ticket(state['ticket_id'])
                        return_message = f"Successfully deleted ticket {state['ticket_id']}"
                    case _:
                        return_message = "Invalid action"

                return {
                    "messages": [
                        ToolMessage(
                            content=return_message,
                            tool_call_id=tool_call_id,
                            name="ticket_tool"
                        )
                    ]
                }

            except Exception as e:
                logger.error(f"Error in delete ticket action: {e}", exc_info=True)
                raise ValueError(f"Error in delete ticket action: {str(e)}")

        except GraphInterrupt as i:
            # Re-raise interrupts to be handled by the message generator
            raise i
        except Exception as e:
            error_msg = f"Error deleting ticket: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state['last_error'] = error_msg
            raise ValueError(error_msg) 