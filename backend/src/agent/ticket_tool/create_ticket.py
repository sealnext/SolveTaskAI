import logging
from typing import Dict, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from agent.configuration import AgentConfiguration
from services.ticketing.client import BaseTicketingClient

logger = logging.getLogger(__name__)

class CreateTicketHandler:
    def __init__(self, ticketing_client: BaseTicketingClient):
        self.client = ticketing_client

    async def create_ticket(self, state: dict) -> dict:
        """Create a ticket and handle human review process."""
        try:
            # Get available issue types and fields
            metadata = await self.client.get_create_issue_metadata()
            available_issue_types = metadata.get('issue_types', [])
            
            # Setup for human review of issue type selection
            last_message = state['messages'][-1]
            tool_call = last_message.tool_calls[0]
            tool_call_id = tool_call['id']
            
            # Present issue types for selection
            human_review = interrupt({
                "question": "Select issue type for the new ticket:",
                "tool_call": tool_call,
                "tool_call_id": tool_call_id,
                "details": {
                    "available_issue_types": available_issue_types
                },
                "available_actions": {
                    "select": {
                        "description": "Select an issue type",
                        "request_format": {
                            "action": "select",
                            "data": {
                                "issue_type_id": "issue-type-id"
                            }
                        }
                    },
                    "cancel": {
                        "description": "Cancel ticket creation",
                        "request_format": {"action": "cancel"}
                    }
                }
            })

            try:
                match human_review["action"]:
                    case "select":
                        issue_type_id = human_review["data"]["issue_type_id"]
                        # Get fields for selected issue type
                        fields_metadata = await self.client.get_create_issue_type_fields(issue_type_id)
                        
                        # Separate required and optional fields
                        required_fields = {}
                        optional_fields = {}
                        
                        for field_id, field_info in fields_metadata.items():
                            if field_info.get('required', False):
                                required_fields[field_id] = field_info
                            else:
                                optional_fields[field_id] = field_info
                        
                        # Present fields for review and input
                        fields_review = interrupt({
                            "question": "Fill in ticket fields:",
                            "tool_call": tool_call,
                            "tool_call_id": tool_call_id,
                            "details": {
                                "required_fields": required_fields,
                                "optional_fields": optional_fields
                            },
                            "available_actions": {
                                "submit": {
                                    "description": "Submit field values",
                                    "request_format": {
                                        "action": "submit",
                                        "data": {
                                            "field_values": {
                                                "field_id": "value"
                                            }
                                        }
                                    }
                                },
                                "cancel": {
                                    "description": "Cancel ticket creation",
                                    "request_format": {"action": "cancel"}
                                }
                            }
                        })
                        
                        match fields_review["action"]:
                            case "submit":
                                field_values = fields_review["data"]["field_values"]
                                
                                # Validate required fields
                                missing_required = [
                                    field_id for field_id in required_fields
                                    if field_id not in field_values
                                ]
                                
                                if missing_required:
                                    raise ValueError(f"Missing required fields: {', '.join(missing_required)}")
                                
                                # Create the ticket
                                ticket_data = {
                                    "issue_type_id": issue_type_id,
                                    **field_values
                                }
                                
                                new_ticket = await self.client.create_ticket(ticket_data)
                                return_message = f"Successfully created ticket: {new_ticket['key']}"
                                state['result'] = return_message
                                return state
                                
                            case "cancel":
                                state['result'] = "Ticket creation cancelled during field input"
                                return state
                            case _:
                                raise ValueError(f"Invalid action during field input: {fields_review['action']}")
                        
                    case "cancel":
                        state['result'] = "Ticket creation cancelled during issue type selection"
                        return state
                    case _:
                        raise ValueError(f"Invalid action during issue type selection: {human_review['action']}")

            except Exception as e:
                logger.error(f"Error in create ticket action: {e}", exc_info=True)
                raise ValueError(f"Error in create ticket action: {str(e)}")

        except GraphInterrupt as i:
            # Re-raise interrupts to be handled by the message generator
            raise i
        except Exception as e:
            error_msg = f"Error creating ticket: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state['last_error'] = error_msg
            raise ValueError(error_msg) 