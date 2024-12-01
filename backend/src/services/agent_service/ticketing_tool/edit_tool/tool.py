from pydantic import BaseModel, Field

import logging
from typing import Dict, Any, Optional

from config import OPENAI_MODEL
from config.enums import TicketingSystemType
from models import Project, APIKey

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from ..jira_client import JiraClient
from .prompts import TICKET_MANAGEMENT_SYSTEM_MESSAGE, create_user_message

logger = logging.getLogger(__name__)

class OutputSchema(BaseModel):
    operation: str = Field(description="The operation to perform on the ticket")
    id: Optional[str] = Field(description="The ID of the element to update")
    fields: Dict[str, Any] = Field(description="The fields to update on the ticket")

def create_edit_ticketing_tool(project: Project, api_key: APIKey):
    """Creates a ticketing tool with project and api_key context."""
    
    # Initialize the client
    client = _initialize_client(project, api_key)
    
    # Initialize LLM for parsing requests
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    parser_llm = llm.with_structured_output(OutputSchema)
    
    @tool("manage_tickets")
    async def manage_tickets(request: str, ticket_id: str) -> str:
        """
        Manages ticket operations (create/update/modify tickets).
        
        Args:
            request: The action to perform on the ticket (e.g., 'Add label TEST')
            ticket_id: The ID of the ticket to update (e.g., 'PZ-2')
            
        Use this tool to update existing tickets with changes like:
        - Update ticket content (title, description, etc)
        - Manage labels and tags
        - Handle comments (add/edit/remove)
        - Change ticket assignments
        - Manage relationships (parent/child, links)
        - Update workflow status
        - Modify planning fields (sprint, custom fields)
        """
        try:
            logger.info(f"🎯 TicketingTool: Processing request for ticket {ticket_id}")
            logger.info(f"🎯 TicketingTool: Request: {request}")
            
            # Get available fields and their metadata
            logger.info(f"🎯 TicketingTool: Fetching ticket and template data for {ticket_id}")
            ticket = await client.get_ticket_and_template_json(ticket_id)
            logger.info(f"🎯 TicketingTool: Received ticket data: {ticket}")
            
            messages = [
                {"role": "system", "content": TICKET_MANAGEMENT_SYSTEM_MESSAGE},
                {"role": "user", "content": create_user_message(
                    request=request,
                    schema_json=ticket.model_dump_json(indent=1)
                )}
            ]
            
            logger.info(f"🎯 TicketingTool: Sending messages to LLM: {messages}")
            response = await parser_llm.ainvoke(messages)
            logger.info(f"🎯 TicketingTool: Received LLM response: {response}")
            
            updates = response.model_dump()
            logger.info(f"🎯 TicketingTool: Parsed updates: {updates}")
            
            # Apply updates
            logger.info(f"🎯 TicketingTool: Applying updates to ticket {ticket_id}")
            result = await client.operation(ticket_id, updates)
            logger.info(f"🎯 TicketingTool: Update result: {result}")
            
            return f"Successfully updated ticket {result['ticket_id']}"
            
        except Exception as e:
            error_msg = f"Failed to process ticketing request: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    return manage_tickets

def _initialize_client(project: Project, api_key: APIKey):
    """Initialize the appropriate client based on project service type."""
    if project.service_type == TicketingSystemType.JIRA:
        return JiraClient(
            domain=api_key.domain,
            api_key=api_key.api_key,
            project_key=project.key,
            domain_email=api_key.domain_email
        )
    elif project.service_type == TicketingSystemType.AZURE:
        raise NotImplementedError("Azure ticketing system not supported yet")
    else:
        raise ValueError(f"Unsupported service type: {project.service_type}")