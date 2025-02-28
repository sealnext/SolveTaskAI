from langchain_core.tools import tool
from typing import Dict, Any, List

@tool("get_issue_types")
async def get_issue_types_tool(project: Project, api_key: APIKey) -> List[Dict[str, Any]]:
    """Get available issue types for the project."""
    client = _initialize_client(project, api_key)
    return await client.get_project_issue_types()

@tool("get_required_fields")
async def get_required_fields_tool(project: Project, api_key: APIKey, issue_type_id: str) -> Dict[str, Any]:
    """Get required fields for a specific issue type."""
    client = _initialize_client(project, api_key)
    return await client.get_issue_type_fields(issue_type_id)

@tool("create_jira_ticket")
async def create_ticket_tool(project: Project, api_key: APIKey, issue_type_id: str, field_values: Dict[str, Any]) -> Dict[str, str]:
    """Create a new ticket with the provided values."""
    client = _initialize_client(project, api_key)
    return await client.create_ticket(issue_type_id, field_values) 