EDIT_TICKET_SYSTEM_PROMPT = """You are an AI Jira Field Mapping Specialist. Your task is to accurately map user requests to Jira fields, ensuring all parts of the request are addressed efficiently and correctly."""

EDIT_TICKET_USER_PROMPT_TEMPLATE = """First, analyze the following user request:

<user_request>
{detailed_query}
</user_request>

Now, review the available Jira fields with their schema, allowed operations, and current values:

<jira_fields>
{available_fields}
</jira_fields>

### Instructions:

1. Analyze the user's request and extract all elements that need to be updated.

2. For each element:
   - Identify the correct Jira field by matching it with the `name` or `customfield_ID` from `jira_fields`.
   - Don't invent new fields, only map to existing ones in jira_fields. 
   - Compare with the field's current value to determine if an update is needed.
   - Verify the requested operation (e.g., `add`, `set`, `remove`) is allowed for that field.
   - Ensure the value format aligns with the field's `type` and `schema`.

3. Create a **`validation`** section for each field:
   - IMPORTANT: Every field in the update section MUST have a corresponding entry in the validation section
   - Use "Needs Validation" status whenever there's uncertainty about IDs, references, or exact values
   - Set appropriate confidence levels (High, Medium, Low)
   - Missing validation info for any field in the update section will cause an error

4. Structure your output as JSON in the following format, only return the raw json:

Disclaimer, this is just an simple example. You need to make you're own json based on the jira_fields and user_request.
</json_example>
{json_example}
</json_example>

### Key Notes:
- Compare your proposed changes with the current values to ensure meaningful updates.
- Derive the correct structure and format dynamically based on the `schema` and `operations` in `jira_fields`.
- Use the **`update`** section for all dynamic changes and the **`validation`** section for confidence and validation information.
- CRITICAL: Every field in the update section MUST have a corresponding entry in the validation section
- If unsure about a mapping, use a lower confidence level and mark it for validation, don't add comments.
- If some fields cannot be mapped, add them to the description as text.
- Instead of adding comments related to placeholder values, just use "Needs Validation" on validation field. Keep the placeholder only.
- Use accountId for user fields (reporter, assignee) - never use names
- Output pure JSON only - no comments or explanations
- Map only to existing jira_fields - unmappable items go in description, don't invent new fields be carefull with that. 

Proceed with your analysis and provide only the JSON output."""

JSON_EXAMPLE = """{
    "update": {
        "summary": [
        {"set": "new title"}
        ],
        "assignee": [
        {"set": {"accountId": "example_id_account"}}
        ],
        "labels": [
        {"add": "security"}
        ],
        "customfield_10020": [
        {"set": 1} 
        ],
        "description": [
        {"set": "new description"}
        ],
        "issuelinks": [
        {
            "add": {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": "PZ-5"}
            }
        }
        ]
    },
    "validation": {
        "summary": {"confidence": "High", "validation": "Valid"},
        "assignee": {"confidence": "High", "validation": "Valid"},
        "labels": {"confidence": "High", "validation": "Valid"},
        "customfield_10020": {"confidence": "Low", "validation": "Needs Validation"},
        "description": {"confidence": "High", "validation": "Valid"},
        "priority": {"confidence": "High", "validation": "Valid"},
        "issuelinks": {"confidence": "Medium", "validation": "Valid"}
    }
}""" 