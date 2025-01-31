EDIT_TICKET_SYSTEM_PROMPT = """You are an AI Jira Field Mapping Specialist. Your task is to accurately map user requests to Jira fields, ensuring all parts of the request are addressed efficiently and correctly."""

EDIT_TICKET_USER_PROMPT_TEMPLATE = """First, review the available Jira fields with their schema, allowed operations, and current values:

<available_fields>
{available_fields}
</available_fields>

Now, analyze the following user request:

<detailed_query>
{detailed_query}
</detailed_query>

### Instructions:

1. Analyze the user's request and extract all elements that need to be updated or set.

2. For each element:
   - Identify the correct Jira field by matching it with the 'name' or 'customfield_ID' from <available_fields>.
   - Only map to existing fields in <available_fields>. Do not invent new fields!
   - Compare with the field's current value to determine if an update is needed and how.
   - Verify the requested operation (e.g., 'add', 'set', 'remove', 'edit') is allowed for that field.
   - Ensure the value format aligns with the field's 'type' and 'schema'.

3. Categorize each update:
   - Use the 'fields' section for complete replacements (e.g., summary, priority, description, story points, epic link, sprint).
   - Use the 'update' section for incremental modifications (e.g., labels, assignee, issuelinks).

4. Create 'validation' section for each field in both 'fields' and 'update' sections:
   - Every field must have a corresponding entry in the validation section.
   - Use "Needs Validation" status whenever there's uncertainty about IDs, references, or exact values.
   - Set appropriate confidence levels (High, Medium, Low).

5. Structure your output as JSON in the following format:

</json_example>
{json_example}
</json_example>

Key Notes:
- Compare your proposed changes with the current values to ensure meaningful updates.
- Derive the correct structure and format based on the 'schema' and 'operations' in <available_fields>.
- If unsure about a mapping, use a lower confidence level and mark it for validation.
- If some fields cannot be mapped, you can't find them in <available_fields>, add them to the description as text!
- Use accountId for user fields (reporter, assignee) - never use names.
- Map only to existing fields in <available_fields> - unmappable items go in description.

Update Operations:
- SET: Sets the value of the field. The incoming value must be the same shape as the value of the field from a GET.
- ADD: Adds an element to a field that is an array.
- REMOVE: Removes an element from a field that is an array.
- EDIT: Edits an element in a field that is an array. The element is indexed/identified by the value itself (usually by id/name/key).

Update Structure:
The general shape of an update is field, array of verb-value pairs. For example:

{{
  "update": {{
    "field1": [ {{"verb": value}}, {{"verb": value}}, ...],
    "field2": [ {{"verb": value}}, {{"verb": value}}, ...]
  }}
}}

Important:
- A given field must appear only in one or the other, "update" or "fields", not both.
- Simple updates (implicit set) should use the "fields" section.
- Fields that cannot be implicitly set (e.g., comments) must use explicit-verb updates in the "update" section.

Before providing the final JSON output, wrap your thought process in <jira_field_mapping_process> tags:
1. List all elements from the user request that need updating, numbered for clarity.
2. For each element:
   - Explicitly match it to a Jira field
   - Note its current value
   - Determine the appropriate update method (fields or update)
   - Assess confidence and validation needs
3. Plan the structure of the JSON output

After your analysis, provide only the JSON output, in <json_output> tags, without any additional comments or explanations in it.
"""

JSON_EXAMPLE = """{{
  "fields": {{
    "summary": "New Issue Summary",
    "description": "Detailed description of the issue",
    "priority": {{"id": "3"}},
    "customfield_10001": 8
  }},
  "update": {{
    "labels": [
      {{"add": "new-label"}}
    ],
    "assignee": [
      {{"set": {{"accountId": "INTRODUCED_ACCOUNT_ID"}}}}
    ]
  }},
  "validation": {{
    "summary": {{"confidence": "High", "validation": "Valid"}},
    "description": {{"confidence": "High", "validation": "Valid"}},
    "priority": {{"confidence": "Medium", "validation": "Needs Validation"}},
    "customfield_10001": {{"confidence": "High", "validation": "Valid"}},
    "labels": {{"confidence": "High", "validation": "Valid"}},
    "assignee": {{"confidence": "Low", "validation": "Needs Validation"}}
  }}
}}"""