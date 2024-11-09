from typing import Dict, Any, List
import aiohttp
import base64
import logging

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, domain: str, api_key: str, project_key: str):
        self.domain = domain
        self.api_key = api_key
        self.project_key = project_key
        self.base_url = f"https://{domain}/rest/api/2"
        self.auth_header = self._create_auth_header(api_key)

    def _create_auth_header(self, api_key: str) -> Dict[str, str]:
        encoded = base64.b64encode(f":{api_key}".encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Jira."""
        url = f"{self.base_url}/issue"
        
        # Prepare the Jira issue data
        issue_data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": task_data["title"],
                "description": task_data["description"],
                "issuetype": {"name": "Task"},
            }
        }

        # Add estimate if provided
        if task_data.get("estimate"):
            issue_data["fields"]["timetracking"] = {
                "originalEstimate": task_data["estimate"]
            }

        # Add parent link if provided
        if task_data.get("parent_ticket"):
            issue_data["fields"]["parent"] = {
                "key": task_data["parent_ticket"]
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=issue_data, headers=self.auth_header) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                result = await response.json()
                return {
                    "key": result["key"],
                    "url": f"https://{self.domain}/browse/{result['key']}"
                } 

    async def update_task(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Jira ticket."""
        url = f"{self.base_url}/issue/{ticket_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json={"fields": updates}, headers=self.auth_header) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                return {"key": ticket_id}

    async def link_tickets(self, source_ticket: str, target_ticket: str, link_type: str) -> None:
        """Create a link between two Jira tickets."""
        url = f"{self.base_url}/issueLink"
        
        link_data = {
            "type": {"name": link_type},
            "inwardIssue": {"key": source_ticket},
            "outwardIssue": {"key": target_ticket}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=link_data, headers=self.auth_header) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get detailed information about a Jira ticket."""
        url = f"{self.base_url}/issue/{ticket_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.auth_header) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                return await response.json()

    async def search_tickets(self, query: str) -> List[Dict[str, Any]]:
        """Search for Jira tickets matching the query."""
        url = f"{self.base_url}/search"
        
        jql = f'project = "{self.project_key}" AND {query}'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"jql": jql}, headers=self.auth_header) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                result = await response.json()
                return result["issues"] 