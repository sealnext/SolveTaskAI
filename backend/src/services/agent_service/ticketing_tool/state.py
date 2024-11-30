from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass, field
from models import Project
from models.apikey import APIKey

@dataclass
class TicketingState:
    """State for the ticketing workflow.
    
    Attributes:
        request (str): The user's request/description
        project (Project): Project context
        api_key (APIKey): API key for authentication
        ticket_id (Optional[str]): ID of existing ticket (if updating)
        issue_type (Optional[Dict[str, Any]]): Selected issue type information
        required_fields (Optional[Dict[str, Any]]): Required fields for the issue type
        field_values (Optional[Dict[str, Any]]): Values for the required fields
        retry_count (int): Number of retry attempts
        max_retries (int): Maximum number of retries allowed
        tools (List[Any]): List of available tools
        edit_tool (Any): Tool for editing/creating tickets
        status (str): Current status of the workflow
        response (Optional[str]): Response from the last operation
    """
    request: str
    project: Project
    api_key: APIKey
    tools: List[Any]
    edit_tool: Any
    ticket_id: Optional[str] = None
    issue_type: Optional[Dict[str, Any]] = None
    required_fields: Optional[Dict[str, Any]] = None
    field_values: Optional[Dict[str, Any]] = None
    retry_count: int = field(default=0)
    max_retries: int = field(default=3)
    status: str = field(default="started")
    response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "request": self.request,
            "project": self.project,
            "api_key": self.api_key,
            "ticket_id": self.ticket_id,
            "issue_type": self.issue_type,
            "required_fields": self.required_fields,
            "field_values": self.field_values,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "tools": self.tools,
            "edit_tool": self.edit_tool,
            "status": self.status,
            "response": self.response
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TicketingState":
        """Create state from dictionary."""
        return cls(**data)