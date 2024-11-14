from typing import Dict, Any, List
import aiohttp
import logging
from aiohttp import BasicAuth

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, domain: str, api_key: str, project_key: str, domain_email: str):
        self.domain = domain.replace("https://", "").replace("http://", "")
        self.api_key = api_key
        self.project_key = project_key
        self.api_version = "2"
        self.base_url = f"https://{self.domain}/rest/api/{self.api_version}"
        self.auth = BasicAuth(domain_email, api_key)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logger.info(f"JiraClient initialized with base_url: {self.base_url} and email: {domain_email}")

    async def get_editmeta_template(self, ticket_id: str) -> Dict[str, Any]:
        """Get the editmeta template for a ticket."""
        url = f"{self.base_url}/issue/{ticket_id}/editmeta"
        logger.info(f"Getting editmeta template for ticket {ticket_id} from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers,
                    auth=self.auth
                ) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        logger.error(f"Jira API error response: {error_data}")
                        raise Exception(f"Jira API error: {error_data}")
                    
                    response_data = await response.json()
                    return response_data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to Jira API: {str(e)}")
            raise Exception(f"Failed to connect to Jira API: {str(e)}")

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
            async with session.post(url, json=issue_data, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                result = await response.json()
                return {
                    "key": result["key"],
                    "url": f"https://{self.domain}/browse/{result['key']}"
                } 

    async def update_task(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Jira ticket.
        
        Supports both direct field updates and operations (set/add/remove).
        Field names are case-sensitive and should match Jira's field names.
        """
        url = f"{self.base_url}/issue/{ticket_id}"
        
        # Convert field names to proper Jira field names (first letter lowercase)
        formatted_updates = {}
        for key, value in updates.items():
            # Convert field names like 'Summary' to 'summary'
            jira_field_name = key[0].lower() + key[1:] if key else key
            formatted_updates[jira_field_name] = value

        # Prepare the request payload
        payload = {
            "fields": formatted_updates
        }
        
        logger.debug(f"Updating Jira ticket {ticket_id} with payload: {payload}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url, 
                json=payload,
                headers=self.headers,
                auth=self.auth
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    logger.error(f"Jira API error response: {error_data}")
                    raise Exception(f"Jira API error: {error_data}")
                
                # Jira returns 204 No Content on successful update
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
            async with session.post(url, json=link_data, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get detailed information about a Jira ticket."""
        url = f"{self.base_url}/issue/{ticket_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                return await response.json()

    async def search_tickets(self, query: str) -> List[Dict[str, Any]]:
        """Search for Jira tickets matching the query."""
        url = f"{self.base_url}/search"
        
        jql = f'project = "{self.project_key}" AND {query}'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"jql": jql}, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")
                
                result = await response.json()
                return result["issues"] 