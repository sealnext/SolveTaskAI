from pydantic import BaseModel, Field

import json
import logging
from typing import Dict, Any, Optional

from config import OPENAI_MODEL
from config.enums import TicketingSystemType
from models import Project, APIKey

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .jira_client import JiraClient

logger = logging.getLogger(__name__)

class OutputSchema(BaseModel):
    operation: str = Field(description="The operation to perform on the ticket")
    id: Optional[str] = Field(description="The ID of the element to update")
    fields: Dict[str, Any] = Field(description="The fields to update on the ticket")

def create_ticketing_tool(project: Project, api_key: APIKey):
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
        - Adding or removing labels
        - Changing status
        - Updating fields
        - Adding comments
        """
        try:
            logger.info(f"🎯 TicketingTool: Processing request for ticket {ticket_id}")
            
            # Get available fields and their metadata
            ticket = await client.get_ticket_and_template_json(ticket_id)
            
            logger.info(f"🎯 TicketingTool: Ticket: {ticket.model_dump_json(indent=1)}")
            
            # Create system message with template structure
            system_message = """
            You are a ticket management assistant. Convert user requests into structured JSON updates for tickets.

            -- RULES:
            1. Match Operation: Ensure the requested operation (`add`, `set`, `remove`, `edit`, `copy`) is supported for the field in `modifiable_fields`.
            2. Extract Value: Use the `value` field in `modifiable_fields` as the current state when constructing the update payload.
            3. Include Operation: Include the `operation` key in the response to reflect the user's requested action.
            4. Payload Structure: Format the payload based on the operation:
            - For `add`, `set`, and `remove`: Use `fields` to reference the field `key`.
            - For `edit` and `copy`: Include additional details like `id` or `resource` fields as needed.
            5. Handle Errors: If the field or operation is unsupported, provide a clear error message.

            -- EXAMPLES:

            1. Add, Set, Remove Operations:
            Request: Add a label "urgent" or set the title to "Updated title" or remove the label "high-priority".
            EditableSchema:
                - { "labels": { "key": "labels", "operations": ["add", "set", "remove"], "value": ["bug", "high-priority"] } }
                - { "summary": { "key": "summary", "operations": ["set"], "value": "Registration Form Fails for Users" } }
            Response (Add): { "operation": "add", "fields": { "labels": ["urgent"] } }
            Response (Set): { "operation": "set", "fields": { "summary": "Updated title" } }
            Response (Remove): { "operation": "remove", "fields": { "labels": ["high-priority"] } }

            2. Edit Operation:
            Request: Edit the comment with ID "10001" to say "Updated text".
            EditableSchema: { "comment": { "key": "comment", "operations": ["add", "edit", "remove"] } }
            Response: { "operation": "edit", "id": "10001", "fields": { "comment": { "body": "Updated text" } } }

            3. Copy Operation:
            Request: Copy the file with ID "file-1234" to this task.
            EditableSchema: { "attachment": { "key": "attachment", "operations": ["set", "copy"] } }
            Response: { "operation": "copy", "fields": { "attachment": { "fileId": "file-1234" } } }
            """
            
            user_message = f"""
            Convert this request into a structured JSON payload.

            -- Request by User:
            ```{request}```
            
            -- EditableSchema (their values and what operations are supported on each field):
            ```{ticket.model_dump_json(indent=1)}```
            """

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
                        
            response = await parser_llm.ainvoke(messages)
            # Convert Pydantic model to dictionary
            updates = response.model_dump()
            
            logger.debug(f"TicketingTool: Parsed response updates: {updates}")
            
            # Apply updates
            result = await client.operation(ticket_id, updates)
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