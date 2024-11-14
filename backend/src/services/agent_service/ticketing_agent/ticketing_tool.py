from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from models import Project, APIKey
from config.enums import TicketingSystemType
import logging
from .jira_client import JiraClient
import json

logger = logging.getLogger(__name__)

def create_ticketing_tool(project: Project, api_key: APIKey):
    """Creates a ticketing tool with project and api_key context."""
    
    # Initialize the client
    client = _initialize_client(project, api_key)
    
    @tool
    async def manage_tickets(request: str, ticket_id: str) -> str:
        """
        Manages ticket operations (create/update/modify tickets).
        
        For adding labels, use update_task with the labels field:
        update_task(ticket_id="PZ-2", updates={"labels": ["TEST"]})
        
        Required arguments:
            request: "action to perform (e.g., Add label TEST)"
            ticket_id: "ticket ID (e.g., PZ-2)"
        
        Example: manage_tickets(request="Add label TEST", ticket_id="PZ-2")
        
        IMPORTANT: For label operations, this tool will translate your request into the appropriate update_task call.
        """
        try:
            logger.info("🎯 TicketingTool: Starting new request processing")
            logger.info(f"Request details - request: {request}, ticket_id: {ticket_id}")
            
            # Process request and return result
            result = await _process_request(client, request, ticket_id)
            return result
            
        except Exception as e:
            error_msg = f"Failed to process ticketing request: {str(e)}"
            logger.error(error_msg)
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

async def _process_request(client: Any, request: str, ticket_id: str) -> str:
    """Process a ticketing request."""
    try:
        # Get available fields and their metadata
        template = await client.get_editmeta_template(ticket_id)
        
        # Parse request and create updates
        updates = _parse_request_to_updates(request, template)
        
        # Apply updates
        result = await client.update_task(ticket_id, updates)
        return f"Successfully updated ticket {result['key']}"
        
    except Exception as e:
        raise Exception(f"Failed to process request: {str(e)}")

def _parse_request_to_updates(request: str, template: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a natural language request into Jira field updates."""
    updates = {}
    
    # Example parsing logic - this should be enhanced based on requirements
    if "label" in request.lower():
        label = request.split("label")[-1].strip().strip("'").strip('"')
        updates["labels"] = [label]
    elif "status" in request.lower():
        status = request.split("status")[-1].strip().strip("'").strip('"')
        updates["status"] = {"name": status}
    
    return updates