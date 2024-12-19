from typing import Dict, Any, List, Tuple, Optional
import aiohttp
import logging
from aiohttp import BasicAuth
from schemas.ticket_schema import EditableTicketSchema
from schemas.status_schema import StatusSchema
from pydantic import parse_obj_as

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

    async def get_issue_type_fields_by_name(self, issue_type_id: str) -> Dict[str, Any]:
        """
        Get the fields for a given issue type by its ID, organized by required and optional fields.

        Args:
            issue_type_id: The ID of the issue type

        Returns:
            Dictionary containing:
                - required_fields: Fields that must be filled
                - optional_fields: Fields that are optional
                Each field contains: name, type, key, operations, allowed_values (if any)

        Raises:
            Exception: If the API call fails
        """
        url = f"{self.base_url}/issue/createmeta"
        params = {
            "projectKeys": self.project_key,
            "issuetypeIds": issue_type_id,
            "expand": "projects.issuetypes.fields"
        }

        logger.debug(f"Fetching fields for issue type ID: {issue_type_id}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    auth=self.auth
                ) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        logger.error(f"Failed to get issue type fields: {error_data}")
                        raise Exception(f"Jira API error: {error_data}")

                    data = await response.json()

                    # Extract fields from response
                    raw_fields = (data.get("projects", [])[0]
                                .get("issuetypes", [])[0]
                                .get("fields", {}))

                    # Organize fields by required/optional
                    required_fields = {}
                    optional_fields = {}

                    for field_key, field_data in raw_fields.items():
                        field_info = {
                            "name": field_data.get("name"),
                            "type": field_data.get("schema", {}).get("type"),
                            "key": field_key,
                            "operations": field_data.get("operations", [])
                        }

                        # Add allowed values if they exist
                        if "allowedValues" in field_data:
                            field_info["allowed_values"] = field_data["allowedValues"]

                        # Add autoCompleteUrl if it exists
                        if "autoCompleteUrl" in field_data:
                            field_info["auto_complete_url"] = field_data["autoCompleteUrl"]

                        # Add custom field info if it's a custom field
                        if "custom" in field_data.get("schema", {}):
                            field_info["custom_type"] = field_data["schema"]["custom"]
                            field_info["custom_id"] = field_data["schema"].get("customId")

                        # Sort into required/optional
                        if field_data.get("required", False):
                            required_fields[field_key] = field_info
                        else:
                            optional_fields[field_key] = field_info

                    return {
                        "required_fields": required_fields,
                        "optional_fields": optional_fields
                    }

        except Exception as e:
            logger.error(f"Error getting issue type fields: {str(e)}")
            raise

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
            # For direct field updates (set operation), use fields payload
            if operation == "set":
                field_updates = {}
                for field_name, value in fields.items():
                    # For fields that need a key-based structure (like parent, assignee, etc)
                    if isinstance(value, (str, int)) and field_name not in ['summary', 'description']:
                        field_updates[field_name] = {"key": value}
                    else:
                        field_updates[field_name] = value
                payload = {"fields": field_updates}
            else:
                # For other operations (add, remove, edit, copy), use update payload
                update_payload = {}
                for field, value in fields.items():
                    operation_entries = []
                    if operation == "add":
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

    async def get_project_issue_types(self) -> List[Dict[str, Any]]:
        """Get available issue types for the project."""
        url = f"{self.base_url}/issue/createmeta/{self.project_key}/issuetypes"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")

                result = await response.json()
                logger.debug(f"Issue types response: {result}")

                # Handle the response structure
                if isinstance(result, dict):
                    # Check for 'issueTypes' (capital T) first
                    if "issueTypes" in result:
                        return result["issueTypes"]
                    # Fallback checks
                    elif "values" in result:
                        return result["values"]
                    elif "issuetypes" in result:  # lowercase version
                        return result["issuetypes"]
                elif isinstance(result, list):
                    return result

                raise Exception("Unexpected response format from Jira API")

    async def get_issue_type_fields(self, issue_type_id: str) -> Dict[str, Any]:
        """Get available fields for a specific issue type."""
        url = f"{self.base_url}/issue/createmeta/{self.project_key}/issuetypes/{issue_type_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, auth=self.auth) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Jira API error: {error_data}")

                return await response.json()

    async def create_ticket(self, issue_type_id: str, field_values: Dict[str, Any]) -> Dict[str, str]:
        """
        Create a new ticket in Jira based on the issue type and its fields.

        Args:
            issue_type_id: The ID of the issue type to create
            field_values: Dictionary containing field values based on the issue type's schema

        Returns:
            Dictionary containing the created ticket ID and URL
        """
        logger.debug(f"jira client - Creating Jira ticket with issue type ID: {issue_type_id} and field values: {field_values}")
        url = f"{self.base_url}/issue"

        # Prepare the issue data with project and issue type
        issue_data = {
            "fields": {
                "project": {"key": self.project_key},
                "issuetype": {"id": issue_type_id},
                **field_values
            }
        }

        logger.debug(f"Creating Jira ticket with payload: {issue_data}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=issue_data,
                    headers=self.headers,
                    auth=self.auth
                ) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        logger.error(f"Jira API error response: {error_data}")
                        raise Exception(f"Failed to create Jira ticket: {error_data}")

                    result = await response.json()
                    ticket_id = result["key"]
                    ticket_url = f"https://{self.domain}/browse/{ticket_id}"

                    logger.info(f"Successfully created Jira ticket: {ticket_id}")

                    return {
                        "ticket_id": ticket_id,
                        "url": ticket_url
                    }

        except Exception as e:
            error_msg = f"Error creating Jira ticket: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def get_project_statuses(self) -> List[StatusSchema]:
        """
        Fetches available statuses for a specific issue type.

        Args:
            issue_type_id: The ID of the issue type

        Returns:
            List of StatusSchema objects
        """
        url = f"{self.base_url}/project/{self.project_key}/statuses"
        logger.debug(f"Fetching statuses for issue types")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    auth=self.auth
                ) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        logger.error(f"Failed to get issue type statuses: {error_data}")
                        raise Exception(f"Jira API error: {error_data}")

                    data = await response.json()

                    # Find statuses for the specific issue type
                    for issue_type in data:
                        statuses = issue_type.get("statuses", [])
                        # Use Pydantic to parse the list of statuses
                        return parse_obj_as(List[StatusSchema], statuses)

                    return []

        except Exception as e:
            logger.error(f"Error getting issue type statuses: {str(e)}")
            raise