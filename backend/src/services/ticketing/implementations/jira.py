from typing import AsyncGenerator, List, Dict, Any
import httpx
from schemas import (
    APIKeySchema, 
    ExternalProjectSchema, 
    JiraIssueSchema, 
    JiraIssueContentSchema,
    JiraProjectResponse,
    JiraSearchResponse
)
from ..client import BaseTicketingClient
from fastapi import HTTPException, status
import asyncio
import logging
from config import (
    JIRA_MAX_RESULTS_PER_PAGE,
    JIRA_MAX_CONCURRENT_REQUESTS,
    JIRA_API_VERSION
)

logger = logging.getLogger(__name__)

class JiraClient(BaseTicketingClient):
    """Jira-specific implementation of the ticketing client."""
    
    BATCH_SIZE = JIRA_MAX_RESULTS_PER_PAGE
    API_VERSION = JIRA_API_VERSION
    
    def __init__(self, http_client: httpx.AsyncClient, api_key: APIKeySchema):
        super().__init__(http_client, api_key)
        self._base_urls: Dict[str, httpx.URL] = {}
        
    def _get_base_url(self) -> httpx.URL:
        """Get or create base URL for the API."""
        if self.api_key.domain not in self._base_urls:
            self._base_urls[self.api_key.domain] = httpx.URL(self.api_key.domain)
        return self._base_urls[self.api_key.domain]
        
    def _build_url(self, *path_segments: str) -> str:
        """Build URL by joining path segments correctly."""
        base_url = self._get_base_url()
        path = f"rest/api/{self.API_VERSION}/" + "/".join(str(segment) for segment in path_segments)
        return str(base_url.join(path))
        
    def _validate_project_key(self, project_key: str) -> None:
        """Validate project key format."""
        if not project_key or not isinstance(project_key, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project key"
            )
    
    def _get_auth_headers(self) -> dict:
        """Get authentication headers for Jira API."""
        import base64
        auth_str = f"{self.api_key.domain_email}:{self.api_key.api_key}"
        auth_bytes = auth_str.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        return {
            "Authorization": f"Basic {base64_auth}",
            "Accept": "application/json"
        }
    
    async def get_projects(self) -> List[ExternalProjectSchema]:
        """Get all projects with efficient pagination."""
        url = self._build_url("project")
        all_projects = []
        start_at = 0
        
        while True:
            params = {
                'startAt': start_at,
                'maxResults': self.BATCH_SIZE
            }
            
            try:
                logger.info(f"Fetching projects from {url} with params {params}")
                data = await self._make_request(
                    "GET", 
                    url, 
                    headers=self._get_auth_headers(), 
                    params=params
                )
                
                # Jira Cloud returns a list directly
                if isinstance(data, list):
                    projects = [ExternalProjectSchema.model_validate(project) for project in data]
                    logger.info("Processing response as Jira Cloud list format")
                else:
                    # Fallback for older Jira versions that return an object
                    projects = [ExternalProjectSchema.model_validate(project) for project in data.get('values', [])]
                    logger.info("Processing response as Jira Server object format")
                
                all_projects.extend(projects)
                logger.info(f"Fetched {len(projects)} projects")
                
                if len(projects) < self.BATCH_SIZE:
                    break
                    
                start_at += self.BATCH_SIZE
                
            except Exception as e:
                logger.error(f"Error fetching projects: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch projects: {str(e)}"
                )
            
        if not all_projects:
            logger.warning(f"No projects found for domain {self.api_key.domain}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No projects found in Jira. Please check your API key and permissions."
            )
            
        return all_projects

    async def _fetch_tickets_batch(self, project_key: str, start_at: int) -> List[JiraIssueSchema]:
        """Fetch a batch of tickets with retry logic."""
        params = {
            "jql": f"project = {project_key}",
            "maxResults": JIRA_MAX_RESULTS_PER_PAGE,
            "startAt": start_at,
            "fields": "summary,description,customfield_10008,comment,status,priority,issuetype,labels,resolution,parent,assignee,reporter,resolutiondate,created,updated,project"
        }
        
        try:
            response = await self._make_request(
                "GET",
                self._build_url("search"),
                headers=self._get_auth_headers(),
                params=params,
                response_model=JiraSearchResponse
            )
            issues = response.get("issues", [])
            return [
                JiraIssueSchema.model_validate({
                    **issue,
                    'project_id': str(issue.get('fields', {}).get('project', {}).get('id'))
                }) 
                for issue in issues
            ]
        except Exception as e:
            logger.error(f"Error fetching tickets batch at {start_at}: {str(e)}")
            raise

    async def get_tickets(self, project_key: str) -> AsyncGenerator[JiraIssueSchema, None]:
        """Get all tickets with efficient batch processing.
        
        Uses concurrent requests while maintaining memory efficiency by streaming tickets.
        """
        self._validate_project_key(project_key)
        
        url = self._build_url("search")
        
        # First, get total number of tickets
        params = {
            'jql': f'project="{project_key}"',  # Escape project key
            'maxResults': 0
        }
        data = await self._make_request(
            "GET", 
            url, 
            headers=self._get_auth_headers(), 
            params=params,
            response_model=JiraSearchResponse
        )
            
        total_tickets = data['total']
        
        # Process in batches
        for start_at in range(0, total_tickets, self.BATCH_SIZE * JIRA_MAX_CONCURRENT_REQUESTS):
            # Create batch of concurrent requests
            batch_tasks = []
            for offset in range(0, min(self.BATCH_SIZE * JIRA_MAX_CONCURRENT_REQUESTS, total_tickets - start_at), self.BATCH_SIZE):
                batch_start = start_at + offset
                batch_tasks.append(self._fetch_tickets_batch(project_key, batch_start))
            
            # Execute batch requests concurrently
            batches = await asyncio.gather(*batch_tasks)
            
            # Stream tickets from batches
            for batch in batches:
                for ticket in batch:
                    yield ticket
                
            # Small delay between large batch groups to prevent overwhelming
            if len(batch_tasks) == JIRA_MAX_CONCURRENT_REQUESTS:
                await asyncio.sleep(0.1)

    async def get_ticket(self, ticket_id: str) -> JiraIssueContentSchema:
        """Get a single ticket by ID."""
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID"
            )
            
        url = self._build_url("issue", ticket_id)
        data = await self._make_request("GET", url, headers=self._get_auth_headers())
        return JiraIssueContentSchema(**data)

    async def delete_ticket(self, ticket_id: str, delete_subtasks: bool = True) -> None:
        """Delete a Jira ticket and optionally its subtasks."""
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket ID")
            
        url = self._build_url("issue", ticket_id)
        params = {"deleteSubtasks": str(delete_subtasks).lower()}
        
        try:
            response = await self.http_client.delete(
                url, 
                headers=self._get_auth_headers(),
                params=params,
                timeout=30.0
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted ticket {ticket_id}")
                return
                
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                404: f"Ticket {ticket_id} not found",
                403: "Permission denied. Check if you have 'Delete Issues' permission.",
                400: "Cannot delete issue with subtasks. Set deleteSubtasks=true to delete with subtasks."
            }.get(e.response.status_code, f"Failed to delete ticket: {str(e)}")
            
            logger.error(f"{error_msg} at URL: {url}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )

    async def get_ticket_edit_issue_metadata(self, ticket_id: str) -> dict:
        """Get the metadata for editing a Jira ticket.
        
        This endpoint returns the fields that can be modified for a specific issue,
        including custom fields and their allowed values.
        
        Args:
            ticket_id (str): The ID or key of the Jira ticket
            
        Returns:
            dict: The ticket's editable field metadata
            
        Raises:
            HTTPException: If the request fails or the ticket is not found
        """
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID"
            )
            
        url = self._build_url("issue", ticket_id, "editmeta")
        
        try:
            response = await self.http_client.get(
                url,
                headers=self._get_auth_headers(),
                timeout=30.0
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                404: f"Ticket {ticket_id} not found",
                403: "Permission denied. Check if you have permission to view this ticket.",
                401: "Authentication failed. Please check your API credentials."
            }.get(e.response.status_code, f"Failed to fetch ticket metadata: {str(e)}")
            
            logger.error(f"{error_msg} at URL: {url}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )
        
    async def get_ticket_fields(self, ticket_id: str, fields: List[str]) -> Dict[str, Any]:
        """Get specific fields for a ticket."""
        url = self._build_url("issue", ticket_id)
        
        # Convert fields list to comma-separated string
        fields_param = ",".join(fields)
        
        params = {
            "fields": fields_param,
            "fieldsByKeys": "false"  # Use field IDs instead of keys for better compatibility
        }
        
        response = await self._make_request(
            "GET", 
            url, 
            headers=self._get_auth_headers(),
            params=params
        )
        
        # Extract just the fields we care about
        return {
            field: response.get("fields", {}).get(field)
            for field in fields
        }