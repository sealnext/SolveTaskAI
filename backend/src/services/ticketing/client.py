from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from schemas import APIKeySchema, ExternalProjectSchema, JiraIssueSchema
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from config import DEFAULT_REQUEST_TIMEOUT
from abc import ABC, abstractmethod

class BaseTicketingClient(ABC):
    """Base class for ticketing system clients."""
    
    DEFAULT_TIMEOUT = DEFAULT_REQUEST_TIMEOUT
    
    def __init__(self, http_client: httpx.AsyncClient, api_key: APIKeySchema, project: Any):
        """Initialize the client with an HTTP client and API key.
        
        Args:
            http_client: Pre-configured httpx.AsyncClient with connection pooling
            api_key: API key configuration for the ticketing system
            project: Project configuration containing project key and other details
        """
        self.http_client = http_client
        self.api_key = api_key
        self.project = project

    async def _make_request(
        self, 
        method: str, 
        url: str, 
        timeout: Optional[float] = None,
        response_model: Optional[type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request with automatic retries using FastAPI's dependency system.
        
        Args:
            method: HTTP method to use
            url: URL to request
            timeout: Request timeout in seconds
            response_model: Optional Pydantic model to validate response
            **kwargs: Additional arguments to pass to httpx.request
        """
        try:
            timeout = timeout or self.DEFAULT_TIMEOUT
            response = await self.http_client.request(
                method, 
                url, 
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            data = response.json()
            
            # Validate response with Pydantic if model provided
            if response_model:
                return response_model.parse_obj(data).dict()
            
            # Allow both dict and list responses
            if not isinstance(data, (dict, list)):
                raise ValueError(f"Expected JSON object or array in response, got {type(data)}")
                
            return data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests"
                )
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=str(e)
            )
        except (ValidationError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid response format: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )

    @abstractmethod
    async def get_projects(self) -> List[ExternalProjectSchema]:
        """Get all projects."""
        raise NotImplementedError
        
    @abstractmethod
    async def get_tickets(self) -> AsyncGenerator[JiraIssueSchema, None]:
        """Get all tickets for the project."""
        raise NotImplementedError
        
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> JiraIssueSchema:
        """Get a single ticket by ID."""
        raise NotImplementedError

    @abstractmethod
    async def delete_ticket(self, ticket_id: str, delete_subtasks: bool = False) -> str:
        """Delete a ticket by ID."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_ticket_edit_issue_metadata(self, ticket_id: str) -> dict:
        """Get the metadata for editing a ticket."""
        raise NotImplementedError
    
    @abstractmethod
    async def search_user(self, query: str) -> dict:
        """Search for a user by name."""
        raise NotImplementedError
    
    @abstractmethod
    async def find_sprint_by_name(self, sprint_name: str) -> dict:
        """Find a sprint by name."""
        raise NotImplementedError
    
    @abstractmethod
    async def search_issue_by_name(self, issue_name: str, max_results: int = 5) -> dict:
        """Search for an issue by name."""
        raise NotImplementedError

    @abstractmethod
    async def get_ticket_fields(self, ticket_id: str, fields: List[str]) -> Dict[str, Any]:
        """Get specific fields for a ticket.
        
        Args:
            ticket_id: The ID of the ticket to get fields for
            fields: List of field names to retrieve (e.g., ["summary", "description", "customfield_10020"])
            
        Returns:
            Dictionary containing the requested fields and their current values
        """
        raise NotImplementedError
    
    @abstractmethod
    async def update_ticket(
        self, 
        ticket_id: str, 
        payload: Dict[str, Any],
        notify_users: bool = False,
        transition_id: Optional[str] = None
    ) -> None:
        """Update a ticket with the provided fields and updates.
        
        Args:
            ticket_id: The ID of the ticket to update
            payload: Dictionary containing 'fields' and/or 'update' sections
            notify_users: Whether to notify watchers
            transition_id: ID of the transition to apply (e.g., for status changes)
        """
        raise NotImplementedError

    @abstractmethod
    async def revert_ticket_changes(
        self,
        ticket_id: str,
        version_number: Optional[int] = None
    ) -> None:
        """Revert ticket changes to a previous version."""
        raise NotImplementedError