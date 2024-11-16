import json
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from models import Project, APIKey
from config.enums import TicketingSystemType
from config import OPENAI_MODEL
import logging
from .jira_client import JiraClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def create_ticketing_tool(project: Project, api_key: APIKey):
    """Creates a ticketing tool with project and api_key context."""
    
    # Initialize the client
    client = _initialize_client(project, api_key)
    
    # Initialize LLM for parsing requests
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    parser_llm = llm.bind(response_format={"type": "json_object"})
    
    @tool("manage_tickets")
    async def manage_tickets(request: str, ticket_id: str) -> str:
        """
        Manages ticket operations (create/update/modify tickets).
        
        Args:
            request: The action to perform on the ticket (e.g., 'Add label TEST')
            ticket_id: The ID of the ticket to update (e.g., 'PZ-2')
            
        Use this tool to update existing tickets with changes like:
        - Adding or removing labels
        - Changing status
        - Updating fields
        - Adding comments
        """
        try:
            logger.info(f"🎯 TicketingTool: Processing request for ticket {ticket_id}")
            
            # Get available fields and their metadata
            template = await client.get_editmeta_template(ticket_id)
            
            # Create system message with template structure
            system_message = f"""You are a ticket management assistant. Your task is to convert natural language requests into structured json updates.
            The available fields and their required format are:
            {json.dumps(template, indent=2)}
            
            Example:
            User request: "Add `[FIXED]` at the end of the current title: `Registration Form Fails for Users`"
            Response: {{"fields": {{"summary": "Registration Form Fails for Users [FIXED]"}}}}
            
            Return ONLY a JSON object with the updates, no explanation."""
            
            # Get structured updates from LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Convert this request into field updates: {request}"}
            ]
            
            logger.debug(f"TicketingTool: Parsing request messages: {messages}")
            
            response = await parser_llm.ainvoke(messages)
            updates = json.loads(response.content)
            
            logger.debug(f"TicketingTool: Parsed response updates: {updates}")
            
            # Apply updates
            result = await client.update_task(ticket_id, updates)
            return f"Successfully updated ticket {result['key']}"
            
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