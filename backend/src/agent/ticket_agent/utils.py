import json
import logging
import re
from typing import Any, Dict, Optional, Literal

from agent.configuration import AgentConfiguration
from services.ticketing.client import BaseTicketingClient

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt

from langchain_core.messages import ToolMessage
from .models import JiraTicketUpdate, ReviewAction, ReviewConfig, TicketAgentState
from .prompts import (
    EDIT_TICKET_SYSTEM_PROMPT,
    EDIT_TICKET_USER_PROMPT_TEMPLATE,
    JSON_EXAMPLE,
)

logger = logging.getLogger(__name__)

def clean_json_response(raw_response: str) -> dict:
    """
    Extract and clean JSON content from LLM response which may contain:
    - Optional <json_output> tags or ```json code blocks
    - Potential code comments
    - Extra text surrounding JSON

    Example valid inputs:
    1. With JSON tags:
    Here's the suggested update:
    <json_output>
    {
        // This is a comment
        "update": {
            "priority": "High" /* inline comment */
        },
        "validation": {...}
    }
    </json_output>
    Please review carefully.

    2. With JSON code block:
    ```json
    {
        "update": { /* inline comment */
            "priority": "High"
        },
        // Comment here
        "validation": {...}
    }
    ```

    3. Without markers:
    {
        "update": { 
            "priority": "High"
        }
    }
    """
    # First try to extract JSON between XML-style tags
    json_matches = re.findall(r'<json_output>(.*?)</json_output>', raw_response, re.DOTALL)
    if not json_matches:
        # Fallback to check for markdown-style code blocks
        json_matches = re.findall(r'```json(.*?)```', raw_response, re.DOTALL)
    
    if json_matches:
        # Use last JSON block if multiple present
        json_content = json_matches[-1].strip()
    else:
        # If no tags found, try processing entire input
        json_content = raw_response.strip()

    # Remove line comments and inline comments
    cleaned = '\n'.join([
        line.split('//')[0].split('#')[0].strip()
        for line in json_content.split('\n')
        if not line.strip().startswith('//') and not line.strip().startswith('#')
    ])
    # Remove /* */ comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Remove trailing commas that break JSON parsing
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    
    return json.loads(cleaned)


async def handle_review_process(
    review_config: ReviewConfig,
    client: BaseTicketingClient
) -> str:
    """Unified review handler with operation-type specific logic."""
    try:
        # For resuming operations when no config is provided
        if not review_config:
            return "Operation completed successfully"

        action_map = {
            "edit": _handle_edit_confirmation,
            "delete": _handle_delete_confirmation
        }

        handler = action_map.get(review_config.get("operation_type"))
        if not handler:
            raise ValueError(f"Unsupported operation type: {review_config.get('operation_type')}")
            
        return await handler(review_config, client)

    except GraphInterrupt as i:
        raise i
    except Exception as e:
        logger.error(f"Review process failed: {str(e)}", exc_info=True)
        return f"Review process error: {str(e)}"

async def _handle_edit_confirmation(
    review_config: ReviewConfig,
    client: BaseTicketingClient
) -> str:
    """Handle edit confirmation."""
    preview_data = review_config.get("preview_data", {})
    # Get final payload from review response
    review_response = interrupt({
        "question": review_config.get("question", ""),
        "ticket": review_config.get("metadata", {}).get("ticket_id"),
        "validation": preview_data.get("validation", {}),
        "payload": {
            "fields": preview_data.get("fields", {}),
            "update": preview_data.get("update", {})
        },
        "available_actions": review_config.get("available_actions", [])
    })

    match review_response.get("action", "none"):
        case ReviewAction.CONFIRM:
            payload = review_response.get("payload")
            ticket = review_response.get("ticket")
            
            if not payload or not ticket:
                raise ValueError("Missing required fields in review response: payload and ticket are required")
                
            return await _handle_direct_confirmation(
                payload,
                ticket, 
                client
            )

        case ReviewAction.CANCEL:
            return "Operation cancelled by user"

        case _:
            raise ValueError(f"Unsupported action: {review_response.get('action', 'none')}")

async def _handle_delete_confirmation(review_config: ReviewConfig, client: BaseTicketingClient) -> str:
    """Execute the actual ticket deletion after confirmation."""
    # Get user confirmation through interrupt
    review_response = interrupt({
        "question": review_config.get("question", ""),
        "ticket": review_config.get("metadata", {}).get("ticket_id", ""),
        "available_actions": review_config.get("available_actions", [])
    })

    if review_response["action"] == ReviewAction.CONFIRM:
        ticket_id = review_response.get("ticket", "")
        if not ticket_id:
            raise ValueError("Ticket ID is required for deletion, but was not provided in the resume process")
        return await client.delete_ticket(ticket_id, delete_subtasks=False)

    return "Deletion cancelled by user"

async def _handle_direct_confirmation(
    jira_payload: Dict[str, Any],
    ticket_id: str,
    client: BaseTicketingClient
) -> str:
    """Validează și aplică payload-ul direct în Jira cu retry logic incorporat."""
    MAX_RETRIES = 2
    current_payload = jira_payload
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            await client.update_ticket(ticket_id, current_payload)
            
            # Get successfully changed fields
            changed_fields = list(current_payload.get('update', {}).keys()) + list(current_payload.get('fields', {}).keys())
            message = f"Successfully applied changes to ticket {ticket_id}"
            
            if changed_fields:
                message += f": {', '.join(changed_fields)} we're changed"
                message += " (these fields were modified - for any unmentioned fields please tell the user that you DIDN'T changed them!)"
                
            return message
            
        except Exception as e:
            if attempt >= MAX_RETRIES:
                raise 
            
            error = e.detail if hasattr(e, 'detail') else str(e)
                
            # Get corrected payload AND track removed fields
            current_payload = await self_correct_payload(
                error=str(e),
                payload=current_payload,
                jira_response=error,
                attempt=attempt
            )

async def self_correct_payload(
    error: str,
    payload: dict,
    jira_response: Optional[str],
    attempt: int
) -> dict:
    """Returns corrected payload based on error analysis."""
    llm = ChatOpenAI(model=AgentConfiguration.model, temperature=0.3)
    
    try:
        response = await llm.ainvoke(f"""
### JIRA Error Analysis (Attempt {attempt + 1}) ###
Error: {error}
API Response: {jira_response or 'N/A'}
Current Payload: {json.dumps(payload, indent=2)}

### Correction Rules ###
1. Analyze error message and fix root cause
2. For invalid fields:
- Remove unsupported/invalid fields immediately
- Keep only fields that are 100% valid
- Never attempt to guess or fix field values
- When in doubt, remove the field entirely
3. For structure issues:
- Fix JSON syntax errors only
- Ensure proper nesting
- Match JIRA field types exactly
4. General rules:
- Make absolute minimal changes
- Never add new fields
- Prefer removing fields over guessing fixes, but if you can resolve the error, DO IT!!!
- If error is field-related, default to removal
""")
        return clean_json_response(response.content)
        
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM correction, using original payload")
        return payload

async def prepare_ticket_fields(ticket_id: str, client: BaseTicketingClient) -> Dict:
    """Fetch and prepare available fields for a ticket."""
    metadata = await client.get_ticket_edit_issue_metadata(ticket_id)
    available_fields = {
        k: {sk: sv for sk, sv in v.items() if sv not in (None, {})}
        for k, v in metadata['fields'].items()
    }
    
    current_values = await client.get_ticket_fields(ticket_id, list(available_fields.keys()))
    
    for field_key in available_fields:
        available_fields[field_key]['current_value'] = current_values.get(field_key)
        
    return available_fields

async def generate_field_updates(
    detailed_query: str,
    available_fields: Dict,
    config: RunnableConfig
) -> Dict:
    """Generate field updates using LLM."""
    agent_config = AgentConfiguration()
    llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature)
    
    response = await llm.ainvoke([{
        "role": "system",
        "content": EDIT_TICKET_SYSTEM_PROMPT
    }, {
        "role": "user",
        "content": EDIT_TICKET_USER_PROMPT_TEMPLATE.format(
            detailed_query=detailed_query,
            available_fields=available_fields,
            json_example=JSON_EXAMPLE
        )
    }])
    
    field_updates = clean_json_response(response.content)
    if not isinstance(field_updates, dict) or "update" not in field_updates or "validation" not in field_updates:
        raise ValueError("Invalid LLM response structure")
        
    return field_updates

def create_review_config(
    ticket_id: str,
    operation_type: Literal["edit", "delete"],
    question: str,
    available_actions: list[ReviewAction],
    field_updates: Optional[Dict] = None
) -> ReviewConfig:
    """Create review configuration for ticket operations."""
    base_config = {
        "operation_type": operation_type,
        "question": question,
        "available_actions": available_actions,
        "expected_payload_schema": JiraTicketUpdate.schema() if operation_type == "edit" else None,
        "metadata": {"ticket_id": ticket_id}
    }
    
    if operation_type == "edit" and field_updates:
        base_config["preview_data"] = {
            "validation": field_updates.get("validation", {}),
            "fields": field_updates.get("fields", {}),
            "update": field_updates.get("update", {})
        }
    
    return ReviewConfig(**base_config)

async def handle_edit_error(e: Exception, state: TicketAgentState, field_updates: Dict) -> Command:
    """Handle errors during ticket editing."""
    if state.retry_count >= 2:
        return Command(
            goto="agent",
            update={
                "internal_messages": [
                    ToolMessage(
                        content=f"Failed to apply changes after 3 attempts. Error: {str(e)}. Please try a different approach.",
                        tool_call_id=state.messages[-1].tool_calls[0]["id"]
                    )
                ],
                "done": True
            }
        )
    
    corrected_payload = await self_correct_payload(
        error=str(e),
        payload=field_updates,
        jira_response=getattr(e, 'response', None),
        attempt=state.retry_count
    )
    
    return Command(
        goto="edit_ticket",
        update={
            "field_updates": corrected_payload,
            "retry_count": state.retry_count + 1
        }
    )

async def handle_account_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira account search logic."""
    result = await client.search_user(value)
    total = result.get("total", 0)
    users = result.get("users", [])

    if total == 1:
        return f"Success! Use this accountId instead of the username: {users[0]['accountId']}"
    elif total > 1:
        user_list = "\n".join([
            f"- {user['displayName']}: {user['accountId']}"
            for user in users
        ])
        return (
            "There are multiple accounts that may match the name, "
            "please use only the accountId for the most relevant name:\n"
            f"{user_list}"
        )
    return f"No accounts found matching '{value}'. Please verify the username and try again."

async def handle_issue_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira issue search logic."""
    result = await client.search_issue_by_name(
        issue_name=value,
        max_results=5
    )
    total = result.get("total", 0)
    issues = result.get("issues", [])

    if total == 1:
        issue = issues[0]
        return f"Success! Use this issue reference instead of the name - Key: {issue['key']}"
    elif total > 1:
        issue_list = "\n".join([
            f"- {issue['fields']['summary']}\n  Key: {issue['key']}"
            for issue in issues
        ])
        return (
            "Multiple matching issues found. Please use the most relevant Key:\n"
            f"{issue_list}"
        )
    return f"No issues found matching '{value}'. Please verify the issue name and try again."

async def handle_sprint_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira sprint search logic."""
    result = await client.find_sprint_by_name(sprint_name=value)
    return f"Successfully found entity, please use the id from the response instead of the raw names: {result}"
