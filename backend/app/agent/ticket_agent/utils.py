import json
import logging
import re
from typing import Any, Dict, Optional, Literal, Union
import asyncio

from app.agent.configuration import AgentConfiguration
from app.service.ticketing.client import BaseTicketingClient

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt

from langchain_core.messages import ToolMessage

from .models import (
    ReviewAction,
    ReviewConfig,
)
from .prompts import (
    EDIT_TICKET_SYSTEM_PROMPT,
    EDIT_TICKET_USER_PROMPT_TEMPLATE,
    JSON_EXAMPLE,
    CREATE_TICKET_SYSTEM_PROMPT,
    CREATE_TICKET_USER_PROMPT_TEMPLATE,
    CREATE_JSON_EXAMPLE,
)

logger = logging.getLogger(__name__)


def clean_json_response(raw_response: str) -> dict:
    """
    Extract and clean JSON content from LLM response which may contain:
    - Optional <json_output> tags or ```json code blocks
    - Field analysis sections
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

    3. With field analysis:
    <field_analysis>
    Analysis content here...
    </field_analysis>
    {
        "fields": {...},
        "validation": {...}
    }

    4. Without markers:
    {
        "update": {
            "priority": "High"
        }
    }
    """
    # First try to extract JSON between XML-style tags
    json_matches = re.findall(
        r"<json_output>(.*?)</json_output>", raw_response, re.DOTALL
    )
    if not json_matches:
        # Fallback to check for markdown-style code blocks
        json_matches = re.findall(r"```json(.*?)```", raw_response, re.DOTALL)

    if json_matches:
        # Use last JSON block if multiple present
        json_content = json_matches[-1].strip()
    else:
        # If no tags found, try to find JSON after field analysis or in raw input
        # Remove field analysis section if present
        cleaned_response = re.sub(
            r"<field_analysis>.*?</field_analysis>", "", raw_response, flags=re.DOTALL
        )
        # Find the first occurrence of a JSON object
        json_match = re.search(r"({[\s\S]*})", cleaned_response.strip())
        if json_match:
            json_content = json_match.group(1).strip()
        else:
            json_content = raw_response.strip()

    # Remove line comments and inline comments
    cleaned = "\n".join(
        [
            line.split("//")[0].split("#")[0].strip()
            for line in json_content.split("\n")
            if not line.strip().startswith("//") and not line.strip().startswith("#")
        ]
    )
    # Remove /* */ comments
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

    # Remove trailing commas that break JSON parsing
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    return json.loads(cleaned)


async def handle_review_process(
    review_config: ReviewConfig, client: BaseTicketingClient
) -> str:
    """Unified review handler with operation-type specific logic."""
    try:
        # For resuming operations when no config is provided
        if not review_config:
            return "Operation completed successfully"

        action_map = {
            "edit": _handle_edit_confirmation,
            "delete": _handle_delete_confirmation,
            "create": _handle_create_confirmation,
        }

        handler = action_map.get(review_config.get("operation_type"))
        if not handler:
            raise ValueError(
                f"Unsupported operation type: {review_config.get('operation_type')}"
            )

        return await handler(review_config, client)

    except GraphInterrupt as i:
        raise i
    except Exception as e:
        logger.error(f"Review process failed: {str(e)}", exc_info=True)
        return f"Review process error: {str(e)}"


async def _handle_edit_confirmation(
    review_config: ReviewConfig, client: BaseTicketingClient
) -> str:
    """Handle edit confirmation."""
    preview_data = review_config.get("preview_data", {})
    # Get final payload from review response
    review_response = interrupt(
        {
            "question": review_config.get("question", ""),
            "ticket": review_config.get("metadata", {}).get("ticket_id"),
            "validation": preview_data.get("validation", {}),
            "payload": {
                "fields": preview_data.get("fields", {}),
                "update": preview_data.get("update", {}),
            },
            "available_actions": review_config.get("available_actions", []),
        }
    )

    action = review_response.get("action", "none")
    if action == ReviewAction.CONFIRM:
        try:
            payload = review_response.get("payload")
            ticket = review_response.get("ticket")

            if not payload or not ticket:
                return "Missing required fields in review response: payload and ticket are required"

            return await _handle_direct_confirmation(payload, ticket, client)
        except Exception as e:
            return f"Failed to apply changes: {str(e)}"
    elif action == ReviewAction.CANCEL:
        return "Operation cancelled by user"
    else:
        return f"Unsupported action: {action}"


async def _handle_delete_confirmation(
    review_config: ReviewConfig, client: BaseTicketingClient
) -> str:
    """Execute the actual ticket deletion after confirmation."""
    # Get user confirmation through interrupt - don't catch GraphInterrupt
    review_response = interrupt(
        {
            "question": review_config.get("question", ""),
            "ticket": review_config.get("metadata", {}).get("ticket_id", ""),
            "available_actions": review_config.get("available_actions", []),
        }
    )

    if review_response["action"] == ReviewAction.CONFIRM:
        try:
            ticket_id = review_response.get("ticket", "")
            if not ticket_id:
                return "Ticket ID is required for deletion, but was not provided in the resume process"
            return await client.delete_ticket(ticket_id, delete_subtasks=False)
        except Exception as e:
            return f"Failed to delete ticket: {str(e)}"

    return "Deletion cancelled by user"


async def _handle_create_confirmation(
    review_config: ReviewConfig, client: BaseTicketingClient
) -> str:
    """Handle create confirmation."""
    preview_data = review_config.get("preview_data", {})
    metadata = review_config.get("metadata", {})

    review_response = interrupt(
        {
            "question": review_config.get("question", ""),
            "project": metadata.get("project_key"),
            "issue_type": metadata.get("issue_type"),
            "validation": preview_data.get("validation", {}),
            "payload": {
                "fields": preview_data.get("fields", {}),
                "update": preview_data.get("update", {}),
            },
            "available_actions": review_config.get("available_actions", []),
        }
    )

    action = review_response.get("action", "none")
    if action == ReviewAction.CONFIRM:
        try:
            payload = review_response.get("payload", {})

            # Ensure payload is a dictionary
            if not isinstance(payload, dict):
                payload = {}

            # Ensure fields exists in payload
            if "fields" not in payload:
                payload["fields"] = {}

            # Ensure update exists in payload
            if "update" not in payload:
                payload["update"] = {}

            # Ensure issuetype exists in fields with proper structure, defaulting to Task if not provided
            if "issuetype" not in payload["fields"]:
                payload["fields"]["issuetype"] = {"name": "Task"}
            elif (
                isinstance(payload["fields"]["issuetype"], dict)
                and "name" not in payload["fields"]["issuetype"]
            ):
                payload["fields"]["issuetype"]["name"] = "Task"
            elif not isinstance(payload["fields"]["issuetype"], dict):
                payload["fields"]["issuetype"] = {"name": "Task"}

            # Ensure project exists in fields, defaulting to the project key from the client
            if "project" not in payload["fields"]:
                payload["fields"]["project"] = {"key": client.project.key}

            # Store the final payload for reporting
            final_payload = {
                "fields": {k: v for k, v in payload["fields"].items()},
                "update": {k: v for k, v in payload["update"].items()},
            }

            # Create the ticket
            result = await client.create_ticket(payload)

            # Check if there was an error
            if "error" in result:
                return f"Failed to create ticket: {result['error']}"

            # Format the payload for better readability
            formatted_payload = json.dumps(final_payload, indent=2)

            # Success case with payload information
            return (
                f"Successfully created ticket: {result.get('url', '')}\n"
                f"Give the user the url so he can see it\n"
                f"The following fields were submitted:\n```json\n{formatted_payload}\n```\n"
                f"Note: Some fields may differ from what was requested."
                f"Please inform the user about these differences and what was actually submitted. Tell the user that only the submitted fields were created"
            )
        except Exception as e:
            return f"Failed to create ticket: {str(e)}"

    elif action == ReviewAction.CANCEL:
        return "Operation cancelled by user"

    else:
        return f"Unsupported action: {action}"


async def _handle_direct_confirmation(
    jira_payload: Dict[str, Any], ticket_id: str, client: BaseTicketingClient
) -> str:
    """Validează și aplică payload-ul direct în Jira cu retry logic incorporat."""
    MAX_RETRIES = 2
    current_payload = jira_payload

    for attempt in range(MAX_RETRIES + 1):
        try:
            await client.update_ticket(ticket_id, current_payload)

            # Get successfully changed fields
            changed_fields = list(current_payload.get("update", {}).keys()) + list(
                current_payload.get("fields", {}).keys()
            )
            message = f"Successfully applied changes to ticket {ticket_id}"

            if changed_fields:
                message += f": {', '.join(changed_fields)} we're changed"
                message += " (these fields were modified - for any unmentioned fields please tell the user that you DIDN'T changed them!)"

            return message

        except Exception as e:
            if attempt >= MAX_RETRIES:
                raise

            error = e.detail if hasattr(e, "detail") else str(e)

            # Get corrected payload AND track removed fields
            current_payload = await self_correct_payload(
                error=str(e),
                payload=current_payload,
                jira_response=error,
                attempt=attempt,
            )

    # This should never be reached, but added for completeness
    return f"Failed to update ticket {ticket_id} after {MAX_RETRIES} attempts"


async def self_correct_payload(
    error: str, payload: dict, jira_response: Optional[str], attempt: int
) -> dict:
    """Returns corrected payload based on error analysis."""
    agent_config = AgentConfiguration()

    llm = agent_config.get_llm(custom_temperature=0.3)

    try:
        response = await llm.ainvoke(
            f"""
### JIRA Error Analysis (Attempt {attempt + 1}) ###
Error: {error}
API Response: {jira_response or "N/A"}
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
"""
        )
        return clean_json_response(response.content)

    except json.JSONDecodeError:
        logger.error("Failed to parse LLM correction, using original payload")
        return payload


async def prepare_ticket_fields(ticket_id: str, client: BaseTicketingClient) -> Dict:
    """Fetch and prepare available fields for a ticket."""
    metadata = await client.get_ticket_edit_issue_metadata(ticket_id)
    available_fields = {
        k: {sk: sv for sk, sv in v.items() if sv not in (None, {})}
        for k, v in metadata["fields"].items()
    }

    current_values = await client.get_ticket_fields(
        ticket_id, list(available_fields.keys())
    )

    for field_key in available_fields:
        available_fields[field_key]["current_value"] = current_values.get(field_key)

    return available_fields


async def generate_field_updates(
    detailed_query: str, available_fields: Dict, config: RunnableConfig
) -> Dict:
    """Generate field updates using LLM."""
    agent_config = AgentConfiguration()

    llm = agent_config.get_llm()

    response = await llm.ainvoke(
        [
            {"role": "system", "content": EDIT_TICKET_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": EDIT_TICKET_USER_PROMPT_TEMPLATE.format(
                    detailed_query=detailed_query,
                    available_fields=available_fields,
                    json_example=JSON_EXAMPLE,
                ),
            },
        ]
    )

    field_updates = clean_json_response(response.content)
    if (
        not isinstance(field_updates, dict)
        or "update" not in field_updates
        or "validation" not in field_updates
    ):
        raise ValueError("Invalid LLM response structure")

    return field_updates


def create_review_config(
    operation_type: Literal["edit", "delete", "create"],
    question: Optional[str] = None,
    available_actions: Optional[list[ReviewAction]] = None,
    ticket_id: Optional[str] = None,
    field_updates: Optional[Dict] = None,
    project_key: Optional[str] = None,
    issue_type: Optional[str] = None,
    field_values: Optional[Dict] = None,
) -> ReviewConfig:
    """Create review configuration for ticket operations.

    Args:
        operation_type: Type of operation (edit/delete/create)
        question: Question to ask during review
        available_actions: List of available actions for review
        ticket_id: ID of ticket for edit/delete operations
        field_updates: Field updates for edit operations
        project_key: Project key for create operations
        issue_type: Issue type for create operations
        field_values: Field values for create operations
    """
    # Set default actions based on operation type (todo if want to extend)
    available_actions = [ReviewAction.CONFIRM, ReviewAction.CANCEL]

    # Set default question based on operation type
    if question is None:
        if operation_type == "edit":
            question = f"Review the proposed changes to ticket {ticket_id}. Would you like to proceed?"
        elif operation_type == "create":
            question = f"Review the new ticket details for project {project_key}. Would you like to proceed?"
        elif operation_type == "delete":
            question = f"Are you sure you want to delete ticket {ticket_id}?"

    base_config = {
        "operation_type": operation_type,
        "question": question,
        "available_actions": available_actions,
        "expected_payload_schema": (
            JiraTicketUpdate.schema() if operation_type in ["edit", "create"] else None
        ),
        "metadata": {},
    }

    # Add operation-specific metadata and preview data
    if operation_type == "edit":
        if not ticket_id:
            raise ValueError("ticket_id is required for edit operations")
        base_config["metadata"]["ticket_id"] = ticket_id
        if field_updates:
            base_config["preview_data"] = {
                "validation": field_updates.get("validation", {}),
                "fields": field_updates.get("fields", {}),
                "update": field_updates.get("update", {}),
            }
    elif operation_type == "create":
        if not project_key or not issue_type:
            raise ValueError(
                "project_key and issue_type are required for create operations"
            )
        base_config["metadata"].update(
            {"project_key": project_key, "issue_type": issue_type}
        )
        if field_values:
            base_config["preview_data"] = {
                "fields": field_values.get("fields", {}),
                "validation": field_values.get("validation", {}),
                "update": field_values.get("update", {}),
            }
    elif operation_type == "delete":
        if not ticket_id:
            raise ValueError("ticket_id is required for delete operations")
        base_config["metadata"]["ticket_id"] = ticket_id

    return ReviewConfig(**base_config)


async def handle_edit_error(
    e: Exception, tool_call_id: str, field_values: Dict
) -> Command:
    """Handle errors during ticket editing."""
    # Initialize retry_count to 0 since we don't have state
    retry_count = 0

    # Ensure field_values is a dictionary
    if field_values is None:
        field_values = {}

    if retry_count >= 2:
        return Command(
            goto="agent",
            update={
                "internal_messages": [
                    ToolMessage(
                        content=f"Failed to apply changes after 3 attempts. Error: {str(e)}. Please try a different approach.",
                        tool_call_id=tool_call_id,
                    )
                ],
                "done": True,
            },
        )

    try:
        corrected_payload = await self_correct_payload(
            error=str(e),
            payload=field_values,
            jira_response=getattr(e, "response", None),
            attempt=retry_count,
        )
    except Exception as e:
        # If payload correction fails, return a simple error message
        return Command(
            goto="agent",
            update={
                "internal_messages": [
                    ToolMessage(
                        content=f"Failed to process the request: {str(e)}. Please try a different approach.",
                        tool_call_id=tool_call_id,
                    )
                ],
                "done": True,
            },
        )

    return Command(
        goto="create_ticket",
        update={
            "field_values": corrected_payload,
            "retry_count": retry_count + 1,
        },
    )


async def handle_account_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira account search logic."""
    result = await client.search_user(value)
    total = result.get("total", 0)
    users = result.get("users", [])

    if total == 1:
        return f"Success! Use this accountId instead of the username: {users[0]['accountId']}"
    elif total > 1:
        user_list = "\n".join(
            [f"- {user['displayName']}: {user['accountId']}" for user in users]
        )
        return (
            "There are multiple accounts that may match the name, "
            "please use only the accountId for the most relevant name:\n"
            f"{user_list}"
        )
    return f"No accounts found matching '{value}'. Please verify the username and try again."


async def handle_issue_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira issue search logic."""
    result = await client.search_issue_by_name(issue_name=value, max_results=5)
    total = result.get("total", 0)
    issues = result.get("issues", [])

    if total == 1:
        issue = issues[0]
        return f"Success! Use this issue reference instead of the name - Key: {issue['key']}"
    elif total > 1:
        issue_list = "\n".join(
            [
                f"- {issue['fields']['summary']}\n  Key: {issue['key']}"
                for issue in issues
            ]
        )
        return (
            "Multiple matching issues found. Please use the most relevant Key:\n"
            f"{issue_list}"
        )
    return f"No issues found matching '{value}'. Please verify the issue name and try again."


async def handle_sprint_search(client: BaseTicketingClient, value: str) -> str:
    """Handle Jira sprint search logic."""
    result = await client.find_sprint_by_name(sprint_name=value)
    return f"Successfully found entity, please use the id from the response instead of the raw names: {result}"


async def prepare_creation_fields(
    project_key: str, issue_type: str, client: BaseTicketingClient
) -> Dict:
    """Fetch and prepare available fields for ticket creation using createmeta."""
    metadata = await client.get_issue_createmeta(project_key, issue_type)

    # Procesăm și filtrăm câmpurile într-un singur loc
    processed_fields = {}
    for field_id, field_data in metadata["fields"].items():
        # Skip empty fields
        if not field_data or (isinstance(field_data, dict) and not field_data):
            continue

        # Skip fields with empty allowed values or empty schema
        if (
            field_data.get("allowedValues", None) == []
            and field_data.get("schema", {}) == {}
        ):
            continue

        field_info = {
            "name": field_data["name"],
            "required": field_data.get("required", False),
        }

        # Adăugăm allowed values doar dacă există și nu sunt goale
        if field_data.get("allowedValues"):
            if field_id in ["priority", "issuetype"]:
                field_info["allowedValues"] = [
                    {"id": v.get("id"), "name": v.get("name")}
                    for v in field_data["allowedValues"]
                ]
            else:
                field_info["allowedValues"] = field_data["allowedValues"]

        # Adăugăm schema doar dacă există și nu e goală
        if field_data.get("schema") and field_data["schema"] != {}:
            field_info["schema"] = field_data["schema"]

        # Adăugăm autoCompleteUrl doar dacă există
        if field_data.get("autoCompleteUrl"):
            field_info["autoCompleteUrl"] = field_data["autoCompleteUrl"]

        processed_fields[field_id] = field_info

    return processed_fields


async def retry_llm_creation(
    llm: Union[ChatOpenAI, ChatGoogleGenerativeAI],
    detailed_query: str,
    available_fields: Dict,
    required_fields: Dict,
    previous_attempt: Optional[Dict] = None,
    max_retries: int = 3,
    retry_count: int = 0,
) -> Dict:
    """Retry LLM ticket creation with structured feedback and validation."""
    # Build error feedback from previous attempt
    error_feedback = ""
    if previous_attempt:
        if "fields" not in previous_attempt:
            error_feedback = "The previous response was invalid. Please provide a response with a 'fields' object."
        else:
            missing_fields = [
                f"{field_id} ({field['name']})"
                for field_id, field in required_fields.items()
                if field_id not in previous_attempt["fields"]
            ]
            if missing_fields:
                error_feedback = f"Missing required fields: {', '.join(missing_fields)}"

    # Construct retry prompt with error context only if there was a previous attempt
    retry_prompt = ""
    if error_feedback:
        retry_prompt = f"""Previous attempt failed. {error_feedback}
Please try again with the original query: {detailed_query}
Ensure ALL required fields are included in your response."""

    # Build message chain with error feedback if available
    messages = [
        {"role": "system", "content": CREATE_TICKET_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": CREATE_TICKET_USER_PROMPT_TEMPLATE.format(
                detailed_query=detailed_query,
                available_fields=available_fields,
                required_fields=required_fields,
                json_example=CREATE_JSON_EXAMPLE,
            ),
        },
    ]
    if retry_prompt:
        messages.extend(
            [
                {
                    "role": "assistant",
                    "content": (
                        json.dumps(previous_attempt, indent=2)
                        if previous_attempt
                        else ""
                    ),
                },
                {
                    "role": "user",
                    "content": f"""Your last response is missing:
{error_feedback}

Required fields reference:
{json.dumps(required_fields, indent=2)}

Please try again with the original query: {detailed_query}""",
                },
            ]
        )

    # Get and validate LLM response
    response = await llm.ainvoke(messages)
    creation_fields = clean_json_response(response.content)

    # Validate response structure
    if not isinstance(creation_fields, dict) or "fields" not in creation_fields:
        if retry_count >= max_retries:
            raise ValueError(
                "Max retries exceeded: Failed to get valid LLM response structure"
            )
        await asyncio.sleep(1)
        return await retry_llm_creation(
            llm=llm,
            detailed_query=detailed_query,
            available_fields=available_fields,
            required_fields=required_fields,
            previous_attempt=creation_fields,
            max_retries=max_retries,
            retry_count=retry_count + 1,
        )

    # Ensure update section exists
    if "update" not in creation_fields:
        creation_fields["update"] = {}

    # Validate required fields
    missing_required = [
        field_id
        for field_id in required_fields
        if field_id not in creation_fields["fields"]
    ]
    if missing_required:
        if retry_count >= max_retries:
            raise ValueError(
                f"Max retries exceeded: Missing required fields - {', '.join(missing_required)}"
            )
        await asyncio.sleep(1)
        return await retry_llm_creation(
            llm=llm,
            detailed_query=detailed_query,
            available_fields=available_fields,
            required_fields=required_fields,
            previous_attempt=creation_fields,
            max_retries=max_retries,
            retry_count=retry_count + 1,
        )

    return creation_fields


async def generate_creation_fields(
    detailed_query: str,
    available_fields: Dict,
) -> Dict:
    """Generate validated ticket fields using LLM with retry logic."""
    agent_config = AgentConfiguration()

    llm = agent_config.get_llm()

    required_fields = {
        field_id: field
        for field_id, field in available_fields.items()
        if field["required"]
    }

    return await retry_llm_creation(
        llm=llm,
        detailed_query=detailed_query,
        available_fields=available_fields,
        required_fields=required_fields,
    )
