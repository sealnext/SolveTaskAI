from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from schemas import (
    APIKeySchema, 
    ExternalProjectSchema, 
    JiraIssueSchema, 
    JiraIssueContentSchema,
    JiraSearchResponse
)

from models import Project
from ..client import BaseTicketingClient
from fastapi import HTTPException, status
import asyncio
import logging
from config import (
    JIRA_MAX_RESULTS_PER_PAGE,
    JIRA_MAX_CONCURRENT_REQUESTS,
    JIRA_API_VERSION
)
import re

logger = logging.getLogger(__name__)

class JiraClient(BaseTicketingClient):
    """Jira-specific implementation of the ticketing client."""
    
    BATCH_SIZE = JIRA_MAX_RESULTS_PER_PAGE
    API_VERSION = JIRA_API_VERSION
    
    def __init__(self, http_client: httpx.AsyncClient, api_key: APIKeySchema, project: Project):
        super().__init__(http_client, api_key, project)
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

    async def _fetch_tickets_batch(self, start_at: int) -> List[JiraIssueSchema]:
        """Fetch a batch of tickets with retry logic."""
        params = {
            "jql": f"project = {self.project.key}",  # Use project from client
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

    async def get_tickets(self) -> AsyncGenerator[JiraIssueSchema, None]:
        """Get all tickets with efficient batch processing.
        
        Uses concurrent requests while maintaining memory efficiency by streaming tickets.
        """
        url = self._build_url("search")
        
        # First, get total number of tickets
        params = {
            'jql': f'project = {self.project.key}',  # Use project from client
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
                batch_tasks.append(self._fetch_tickets_batch(batch_start))
            
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

    async def delete_ticket(self, ticket_id: str, delete_subtasks: bool = False) -> str:
        """Delete a Jira ticket and optionally its subtasks.
        
        Args:
            ticket_id: The ID or key of the issue to delete
            delete_subtasks: If True, deletes the issue's subtasks when the issue is deleted
            
        Returns:
            str: Success message
            
        Raises:
            HTTPException: If deletion fails or if trying to delete an issue with subtasks
                         without setting delete_subtasks=True
        """
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID"
            )
            
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
                message = f"Ticket {ticket_id} deleted successfully"
                if delete_subtasks:
                    message += " (including subtasks)"
                logger.info(message)
                return message
                
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                400: "Please return and tell the user that you cannot delete issue with subtasks. Set deleteSubtasks=true to delete with subtasks: " + e.response.text,
                403: "Please return and tell the user that you do not have permission to delete issues. Check if you have 'Browse projects' and 'Delete issues' permissions: " + e.response.text,
                404: f"Please return and tell the user that the ticket {ticket_id} does not exist and he should check the ticket ID",
                401: "Please return and tell the user that your API credentials are invalid. Please check your API credentials: " + e.response.text
            }.get(e.response.status_code, f"Failed to delete ticket: {e.response.text}")
            
            logger.error(f"Error deleting ticket {ticket_id}: {error_msg}")
            logger.error(f"Response content: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )
        except Exception as e:
            logger.error(f"Unexpected error deleting ticket {ticket_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete ticket: {str(e)}"
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

    async def search_user(self, query: str) -> Dict[str, Any]:
        """Search for Jira users based on a query string.
        
        Args:
            query (str): Search string to match against username, display name, or email
            
        Returns:
            Dict[str, Any]: Dictionary containing matched users and metadata
            
        Raises:
            HTTPException: If the request fails or invalid parameters are provided
        """
        if not query or not isinstance(query, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid search query"
            )
            
        url = self._build_url("user", "picker")
        params = {
            "query": query,
            "maxResults": 5
        }
        
        try:
            response = await self._make_request(
                "GET",
                url,
                headers=self._get_auth_headers(),
                params=params
            )
            
            return response
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                403: "Permission denied. Check if you have permission to view users.",
                401: "Authentication failed. Please check your API credentials."
            }.get(e.response.status_code, f"Failed to search users: {str(e)}")
            
            logger.error(f"{error_msg} at URL: {url}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )

    async def get_project_boards(self, project_key_or_id: str) -> List[Dict[str, Any]]:
        """Get all boards for a specific project.
        
        Args:
            project_key_or_id (str): Project key or ID to fetch boards for
            
        Returns:
            List[Dict[str, Any]]: List of board objects associated with the project
            
        Raises:
            HTTPException: If the request fails or the project is not found
        """
        if not project_key_or_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project key or ID is required"
            )
            
        url = "rest/agile/1.0/board"
        params = {
            "projectKeyOrId": project_key_or_id
        }
        
        try:
            response = await self._make_request(
                "GET",
                url,
                headers=self._get_auth_headers(),
                params=params
            )
            
            return response.get("values", [])
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                404: f"Project {project_key_or_id} not found",
                403: "Permission denied. Check if you have access to this project.",
                401: "Authentication failed. Please check your API credentials."
            }.get(e.response.status_code, f"Failed to fetch project boards: {str(e)}")
            
            logger.error(f"{error_msg} for project {project_key_or_id}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )

    async def get_board_sprints(self, board_id: int) -> List[Dict[str, Any]]:
        """Get all sprints for a specific board.
        
        Args:
            board_id (int): The ID of the board to fetch sprints from
            
        Returns:
            List[Dict[str, Any]]: List of sprint objects
            
        Raises:
            HTTPException: If the request fails or the board is not found
        """
        url = f"rest/agile/1.0/board/{board_id}/sprint"
        
        try:
            response = await self._make_request(
                "GET",
                url,
                headers=self._get_auth_headers()
            )
            
            return response.get("values", [])
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                404: f"Board {board_id} not found",
                403: "Permission denied. Check if you have access to this board.",
                401: "Authentication failed. Please check your API credentials."
            }.get(e.response.status_code, f"Failed to fetch board sprints: {str(e)}")
            
            logger.error(f"{error_msg} for board {board_id}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )

    async def find_sprint_by_name(self, sprint_name: str) -> List[Dict[str, Any]]:
        """Find sprints by name across all project boards."""
        try:
            # Use the project key from the project object
            if not self.project or not hasattr(self.project, 'key'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No project key available"
                )

            # Get all boards for the project
            boards = await self.get_project_boards(self.project.key)
            
            matching_sprints = []
            
            # For each board, get its sprints
            for board in boards:
                sprints = await self.get_board_sprints(board["id"])
                
                for sprint in sprints:
                    matching_sprints.append({
                        **sprint,
                        "board_name": board["name"]
                    })
            
            return matching_sprints
            
        except Exception as e:
            logger.error(f"Error searching for sprint '{sprint_name}' in project {self.project.key if hasattr(self.project, 'key') else 'unknown'}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search for sprint: {str(e)}"
            )

    async def search_issue_by_name(
        self, 
        issue_name: str, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search for issues by name (summary) or key using JQL."""
        logger.info(f"Searching for issue with name: '{issue_name}'")
        
        if not issue_name or not isinstance(issue_name, str):
            logger.error("Invalid issue name provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid issue name or key"
            )

        # Ensure we have a project key
        if not self.project or not hasattr(self.project, 'key'):
            logger.error("No project key available in self.project")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No project key available"
            )

        # If it looks like a Jira key (e.g., PZ-123), search by key
        is_key_pattern = bool(re.match(r'^[A-Z]+-\d+$', issue_name))
        logger.info(f"Is key pattern match: {is_key_pattern}")
        
        if is_key_pattern:
            jql = f'project = {self.project.key} AND key = "{issue_name}"'
        else:
            # Escape special characters in the issue name for JQL
            escaped_name = issue_name.replace('"', '\\"')
            jql = f'project = {self.project.key} AND summary ~ "{escaped_name}"'
        
        logger.info(f"Generated JQL query: {jql}")

        url = self._build_url("search")
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "key"
        }
        
        logger.info(f"Making request to URL: {url}")
        logger.info(f"With params: {params}")
        
        try:
            response = await self._make_request(
                "GET",
                url,
                headers=self._get_auth_headers(),
                params=params
            )
            
            issues = response.get("issues", [])
            logger.info(f"Received {len(issues)} issues from Jira")
            
            return {
                "issues": issues,
                "total": len(issues),
                "header": f"Showing {len(issues)} matching issues"
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                403: "Permission denied. Check if you have permission to view issues.",
                401: "Authentication failed. Please check your API credentials."
            }.get(e.response.status_code, f"Failed to search issues: {str(e)}")
            
            logger.error(f"HTTP Error {e.response.status_code}: {error_msg}")
            logger.error(f"Response content: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )

    async def update_ticket(
        self, 
        ticket_id: str, 
        payload: Dict[str, Any],
        notify_users: bool = False,
        transition_id: Optional[str] = None
    ) -> str:
        """Update a Jira ticket with the provided fields and updates.
        
        Args:
            ticket_id (str): The ID or key of the ticket to update
            payload (Dict[str, Any]): The update payload containing 'fields' and/or 'update' sections
            notify_users (bool, optional): Whether to notify watchers. Defaults to True.
            transition_id (str, optional): ID of the transition to apply (e.g., for status changes)
            
        Raises:
            HTTPException: If the request fails or the ticket cannot be updated
        """
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID"
            )
            
        url = self._build_url("issue", ticket_id)
        params = {
            "notifyUsers": str(notify_users).lower(),
            "overrideScreenSecurity": "false",
            "overrideEditableFlag": "false"
        }
        
        # Add minimal history metadata for better tracking
        jira_payload = {
            "fields": payload.get("fields", {}),
            "update": payload.get("update", {}),
            "historyMetadata": {
                "type": "AI_UPDATE",
                "description": "Update made via AI Assistant",
                "activityDescription": "AI Assistant update",
                "actor": {
                    "type": "application",
                    "displayName": "AI Ticket Assistant"
                }
            }
        }
        
        # Add transition if provided
        if transition_id:
            jira_payload["transition"] = {"id": transition_id}
        
        try:
            response = await self.http_client.put(
                url,
                headers={
                    **self._get_auth_headers(),
                    "Content-Type": "application/json"
                },
                params=params,
                json=jira_payload,
                timeout=30.0
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully updated ticket {ticket_id}")
                return f"Ticket {ticket_id} updated successfully"
                
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            error_msg = {
                400: "Invalid fields or updates provided: " + e.response.text,
                403: "Permission denied. Check if you have 'Edit Issues' permission." + e.response.text,
                404: f"Ticket {ticket_id} not found" + e.response.text,
                401: "Authentication failed. Please check your API credentials." + e.response.text
            }.get(e.response.status_code, f"Failed to update ticket: {e.response.text}")
            
            logger.error(f"Error updating ticket {ticket_id}: {error_msg}")
            logger.error(f"Response content: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )
        except Exception as e:
            logger.error(f"Unexpected error updating ticket {ticket_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update ticket: {str(e)}"
            )

    async def revert_ticket_changes(
        self,
        ticket_id: str,
        version_number: Optional[int] = None  # If None, reverts to previous version
    ) -> None:
        """Revert changes made to a Jira ticket to a previous version.
        
        Args:
            ticket_id (str): The ID or key of the ticket to revert
            version_number (int, optional): Specific version to revert to. If None, reverts to previous version.
            
        Raises:
            HTTPException: If the revert fails or the ticket/version cannot be found
        """
        if not ticket_id or not isinstance(ticket_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID"
            )
            
        try:
            # First get the ticket versions/history
            history_url = self._build_url("issue", ticket_id, "changelog")
            history = await self._make_request(
                "GET",
                history_url,
                headers=self._get_auth_headers()
            )
            
            if not history.get("values"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No changes found to revert"
                )
            
            # Get target version
            target_version = None
            if version_number is not None:
                target_version = next(
                    (v for v in history["values"] if v.get("id") == str(version_number)), 
                    None
                )
                if not target_version:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Version {version_number} not found"
                    )
            else:
                # Get previous version
                if len(history["values"]) < 2:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No previous version found to revert to"
                    )
                target_version = history["values"][-2]  # Get second to last version
            
            # Build revert payload from the version
            revert_payload = {
                "update": {},
                "fields": {},
                "historyMetadata": {
                    "type": "AI_REVERT",
                    "description": f"Reverted to version {target_version.get('id')}",
                    "activityDescription": "AI Assistant revert operation",
                    "actor": {
                        "type": "application",
                        "displayName": "AI Ticket Assistant"
                    }
                }
            }
            
            # Apply the reverse of each change
            for item in target_version.get("items", []):
                field = item.get("field")
                from_string = item.get("fromString")
                from_id = item.get("from")  # For fields that use IDs
                
                if field:
                    if field in ["summary", "description", "environment"]:
                        # Text fields use direct string values
                        if from_string is not None:
                            revert_payload["fields"][field] = from_string
                    elif field in ["assignee", "reporter", "creator"]:
                        # User fields need accountId
                        if from_id:
                            revert_payload["fields"][field] = {"accountId": from_id}
                    elif field in ["priority", "issuetype", "status"]:
                        # Fields that use ID references
                        if from_id:
                            revert_payload["fields"][field] = {"id": from_id}
                    elif field in ["labels", "components", "fixVersions"]:
                        # Array fields need special handling
                        if from_string is not None:
                            revert_payload["update"][field] = [{"set": from_string.split(",")}]
                    else:
                        # Default to update operation for other fields
                        if from_string is not None:
                            revert_payload["update"][field] = [{"set": from_string}]
            
            # Make the revert request
            url = self._build_url("issue", ticket_id)
            response = await self.http_client.put(
                url,
                headers={
                    **self._get_auth_headers(),
                    "Content-Type": "application/json"
                },
                json=revert_payload,
                timeout=30.0
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully reverted ticket {ticket_id} to version {target_version.get('id')}")
                return
                
            response.raise_for_status()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to revert ticket {ticket_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revert ticket: {str(e)}"
            )