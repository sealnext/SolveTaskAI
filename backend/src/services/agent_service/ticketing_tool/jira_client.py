
from typing import Dict, Any, List, Tuple, Optional
import aiohttp
import logging
from aiohttp import BasicAuth
from schemas.ticket_schema import EditableTicketSchema

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
        
    async def operation(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a single operation on a Jira ticket.

        Args:
            ticket_id: The ID of the Jira ticket to update.
            updates: A dictionary containing the operation, fields, and optional ID.

        Returns:
            A dictionary with the operation status and ticket ID.
        """

        # Validate the operation payload
        operation = updates.get("operation")
        if not operation:
            raise ValueError("Missing 'operation' in updates payload.")
        if "fields" not in updates:
            raise ValueError("Missing 'fields' in updates payload.")

        fields = updates["fields"]
        operation_id = updates.get("id")  # Optional ID for certain operations

        # Format fields to match Jira's expected structure
        formatted_fields = self.format_fields(fields)

        # Determine the HTTP method, URL, payload, and headers based on the operation
        try:
            method, url, payload, headers = self.construct_request(
                operation, ticket_id, formatted_fields, operation_id
            )
        except ValueError as e:
            logger.error(str(e))
            raise

        # Log the operation
        logger.debug(
            f"Performing {operation} operation on Jira ticket {ticket_id} with payload: {payload}"
        )

        # Make the HTTP request
        try:
            async with aiohttp.ClientSession() as session:
                await self.execute_request(session, method, url, payload, headers)
        except Exception as e:
            logger.error(
                f"Failed to perform {operation} operation on ticket {ticket_id}: {str(e)}"
            )
            raise

        return {"status": "success", "ticket_id": ticket_id, "operation": operation}

    def format_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the fields dictionary to match Jira's expected structure.
        """
        return {
            key[0].lower() + key[1:] if key else key: value
            for key, value in fields.items()
        }

    def construct_request(
    self,
    operation: str,
    ticket_id: str,
    fields: Dict[str, Any],
    operation_id: Optional[str] = None,
) -> Tuple[str, str, Optional[Dict[str, Any]], Dict[str, str]]:
        """
        Construct the HTTP method, URL, payload, and headers based on the operation.

        Returns:
            A tuple of (method, url, payload, headers).
        """
        base_url = f"{self.base_url}/issue/{ticket_id}"
        method = "PUT"  # Use PUT method for all update operations by default
        url = base_url
        payload: Optional[Dict[str, Any]] = {}
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'  # Ensure Content-Type header is set

        if operation in ["set", "edit", "add", "remove", "copy"]:
            # Build the update payload
            update_payload = {}

            for field, value in fields.items():
                operation_entries = []

                # Handle 'add', 'remove', 'set', 'edit', 'copy' operations
                if operation == "set":
                    operation_entries.append({"set": value})
                elif operation == "add":
                    if isinstance(value, list):
                        for item in value:
                            operation_entries.append({"add": item})
                    else:
                        operation_entries.append({"add": value})
                elif operation == "remove":
                    if isinstance(value, list):
                        for item in value:
                            operation_entries.append({"remove": item})
                    else:
                        operation_entries.append({"remove": value})
                elif operation == "edit":
                    if not operation_id:
                        raise ValueError("Missing 'id' for edit operation.")
                    # Assuming 'edit' operation is for comments or similar fields
                    edit_content = {"id": operation_id}
                    if isinstance(value, dict):
                        edit_content.update(value)
                    else:
                        edit_content["body"] = value
                    operation_entries.append({"edit": edit_content})
                elif operation == "copy":
                    operation_entries.append({"copy": value})

                update_payload[field] = operation_entries

            payload = {"update": update_payload}

        else:
            raise ValueError(f"Unsupported operation '{operation}'.")

        if operation == "copy" and "attachment" in fields:
            method = "POST"
            url = f"{base_url}/attachments"
            headers["X-Atlassian-Token"] = "no-check"  # Required for attachments

        return method, url, payload, headers

    async def execute_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]],
        headers: Dict[str, str],
    ) -> None:
        """
        Execute the HTTP request.

        Raises:
            Exception: If the response status is >= 400.
        """
        request_method = getattr(session, method.lower())
        try:
            async with request_method(
                url, json=payload, headers=headers, auth=self.auth
            ) as response:
                logger.debug(f"Request Method: {method}")
                logger.debug(f"Request URL: {url}")
                logger.debug(f"Request Headers: {headers}")
                logger.debug(f"Request Payload: {payload}")
                logger.debug(f"Response Status: {response.status}")
                logger.debug(f"Response Headers: {response.headers}")
                response_text = await response.text()
                logger.debug(f"Response Text: {response_text}")
                await self.handle_response(response)
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise

    async def handle_response(self, response: aiohttp.ClientResponse) -> None:
        """
        Handle the HTTP response, raising an exception for error statuses.

        Raises:
            Exception: If the response status is >= 400.
        """
        if response.status >= 400:
            try:
                error_data = await response.json()
            except aiohttp.ContentTypeError:
                # Response is not JSON
                error_data = await response.text()
            logger.error(f"Jira API error response: {error_data}")
            logger.error(f"Response status: {response.status}")
            logger.error(f"Response headers: {response.headers}")
            logger.error(f"Request URL: {response.url}")
            logger.error(f"Request method: {response.method}")
            raise Exception(f"Jira API error: {error_data}")
    
    async def get_ticket_and_template_json(self, ticket_id: str) -> EditableTicketSchema:
        """Get the ticket and editmeta template for a ticket."""
        url = f"{self.base_url}/issue/{ticket_id}?expand=editmeta"
        logger.info(f"Getting ticket and editmeta template for ticket {ticket_id} from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, auth=self.auth) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        raise Exception(f"Jira API error: {error_data}")
                    
                    result = await response.json()
                    return EditableTicketSchema(**result)
                
        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to Jira API: {str(e)}")
            raise Exception(f"Failed to connect to Jira API: {str(e)}")
                    
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
        
        logger.debug(f"Updating Jira ticket {ticket_id} with payload: {formatted_updates}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url, 
                json=formatted_updates,
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