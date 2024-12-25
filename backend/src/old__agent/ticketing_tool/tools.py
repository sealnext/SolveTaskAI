import logging
from langchain_core.tools import tool
from typing import Dict, Any, List
from models import Project, APIKey
from .jira_client import JiraClient
from .edit_tool.tool import create_edit_ticketing_tool

logger = logging.getLogger(__name__)

def create_ticketing_tools(project: Project, api_key: APIKey) -> List[Any]:
    """Creates all tools needed for ticketing operations."""
    
    client = JiraClient(
        domain=api_key.domain,
        api_key=api_key.api_key,
        project_key=project.key,
        domain_email=api_key.domain_email
    )
    
    logger.debug(f"++++----------------------- Created Jira client for project: {project.key}")
    
    # Get the edit tool
    edit_tool = create_edit_ticketing_tool(project, api_key)
        
    @tool("get_issue_types")
    async def get_issue_types() -> str:
        """
        Get available issue types for the project.
        Use this when you need to know what types of tickets can be created.
        """
        logger.debug("TOOL CALLED: ++++----------------------- Getting issue types")
        response = await client.get_project_issue_types()
        
        logger.info(f"Response: {response}")
        
        try:
            issue_types = response.get('issueTypes', response) if isinstance(response, dict) else response
            
            if not isinstance(issue_types, list):
                raise ValueError(f"Unexpected issue_types format: {type(issue_types)}")
                
            formatted_response = "Available issue types:\n"
            for issue_type in issue_types:
                name = issue_type.get('name', 'Unknown')
                id = issue_type.get('id', 'Unknown')
                description = issue_type.get('description', 'No description available')
                formatted_response += f"- {name} (ID: {id}): {description}\n"
                
            logger.debug(f"Formatted issue types response: {formatted_response}")
            return formatted_response
            
        except Exception as e:
            error_msg = f"Error processing issue types: {str(e)}"
            logger.error(error_msg)
            return error_msg

    @tool("get_required_fields")
    async def get_required_fields(issue_type_id: str) -> Dict[str, Any]:
        """
        Get required fields for a specific issue type.
        Use this when you need to know what fields are needed for a specific ticket type.
        
        Args:
            issue_type_id: The ID of the issue type to get fields for
        """
        logger.info(f"TOOL CALED: ++++----------------------- Getting required fields for issue type: {issue_type_id}")
        return await client.get_issue_type_fields(issue_type_id)

    @tool("get_ticket_info")
    async def get_ticket_info(ticket_id: str) -> Dict[str, Any]:
        """
        Get information about a specific ticket.
        Use this when you need details about an existing ticket.
        
        Args:
            ticket_id: The ID of the ticket to get info for (e.g., 'PZ-123')
        """
        logger.info(f"TOOL CALED: ++++----------------------- Getting ticket info for ticket: {ticket_id}")
        return await client.get_ticket(ticket_id)
    
    @tool("get_ticket_template")
    async def get_ticket_template(issue_type_id: str) -> str:
        """
        Get the template with required and optional fields for creating a specific type of ticket.
        Use this before creating a ticket to understand what fields are needed and their format.
        
        Args:
            issue_type_id: The ID of the issue type (e.g. "10007" for Task)
        """
        logger.info(f"[get_ticket_template] - TOOL CALLED: Getting template for issue type ID: {issue_type_id}")
        
        try:
            # Get fields for this issue type
            fields = await client.get_issue_type_fields(issue_type_id)
            
            logger.debug(f"[get_ticket_template] - Fields: {fields}")
            
            return fields
        except Exception as e:
            logger.error(f"Error getting template: {e}", exc_info=True)
            return f"Failed to get template: {str(e)}"

    @tool("create_ticket")
    async def create_ticket(request: Dict[str, Any], issue_type_id: str) -> str:
        """
        Create a new ticket with the specified details.
        Use this when you need to create a new ticket.
        
        Args:
            request: A dictionary containing the ticket fields
            issue_type_id: The ID of the issue type (get this from get_issue_types response)
        """
        logger.debug(f"Creating ticket with issue type ID: {issue_type_id}")
        
        try:
            result = await client.create_ticket(issue_type_id, request)
            return f"Successfully created ticket: {result['ticket_id']}"
        except Exception as e:
            logger.error(f"Error creating ticket: {e}", exc_info=True)
            return f"Failed to create ticket: {str(e)}"

    @tool("edit_ticket")
    async def edit_ticket(
        ticket_id: str,
        changes: str
    ) -> str:
        """
        Edit an existing ticket with the specified changes.
        Use this when you need to modify an existing ticket.
        
        Args:
            ticket_id: The ID of the ticket to edit (e.g., 'PZ-123')
            changes: Description of changes to make (e.g., "Add label 'urgent', change status to 'In Progress'")
        """
        logger.debug(f"Editing ticket: {ticket_id}")
        return await edit_tool.ainvoke({
            "request": changes,
            "ticket_id": ticket_id
        })

    return [
        get_issue_types,
        create_ticket,
        edit_ticket,
        get_ticket_template
    ] 