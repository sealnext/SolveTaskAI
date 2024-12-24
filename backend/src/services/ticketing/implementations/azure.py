from typing import AsyncGenerator, List, Dict
import httpx
from schemas import APIKeySchema, ExternalProjectSchema, JiraIssueSchema
from ..client import BaseTicketingClient

class AzureClient(BaseTicketingClient):
    """Azure DevOps-specific implementation of the ticketing client."""
    
    async def get_projects(self, api_key: APIKeySchema) -> List[ExternalProjectSchema]:
        headers = self._get_auth_headers(api_key)
        url = f"https://dev.azure.com/{api_key.organization}/_apis/projects"
        data = await self._make_request("GET", url, headers=headers)
        return [ExternalProjectSchema(**project) for project in data['value']]
        
    async def get_tickets(self, api_key: APIKeySchema, project_key: str) -> AsyncGenerator[JiraIssueSchema, None]:
        # TODO: Implement Azure-specific ticket fetching
        raise NotImplementedError("Azure ticket fetching not implemented yet")

    def _get_auth_headers(self, api_key: APIKeySchema) -> dict:
        return {
            "Authorization": f"Bearer {api_key.api_key}",
            "Accept": "application/json"
        }
