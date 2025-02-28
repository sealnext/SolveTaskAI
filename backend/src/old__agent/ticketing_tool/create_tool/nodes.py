from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .prompts import *

async def process_issue_type_selection(
    state: TicketCreationState,
    issue_types: List[Dict[str, Any]]
) -> TicketCreationState:
    """Process issue type selection step."""

    # Format issue types for prompt
    issue_types_str = "\n".join([
        f"- ID: {it['id']} - {it['name']}: {it.get('description', 'No description')}"
        for it in issue_types
    ])

    # Create messages for LLM
    messages = [
        {"role": "system", "content": ISSUE_TYPE_SELECTION_PROMPT.format(
            issue_types=issue_types_str
        )},
        *[{"role": m.type, "content": m.content} for m in state["messages"]]
    ]

    # Get LLM response
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    response = await llm.ainvoke(messages)

    # Update state
    state["messages"].append(AIMessage(content=response.content))

    # Try to extract issue type ID from response
    # (Implementation needed for parsing issue type ID from response)

    return state

async def process_required_fields(
    state: TicketCreationState,
    fields_meta: Dict[str, Any]
) -> TicketCreationState:
    """Process required fields collection step."""

    # Format fields for prompt
    required_fields = {
        name: field for name, field in fields_meta["fields"].items()
        if field.get("required", False)
    }

    fields_str = "\n".join([
        f"- {field['name']}: {field.get('description', 'No description')}"
        for field in required_fields.values()
    ])

    # Create messages for LLM
    messages = [
        {"role": "system", "content": REQUIRED_FIELDS_PROMPT.format(
            issue_type_name=state["issue_type"]["name"],
            required_fields=fields_str,
            current_values=state.get("field_values", {})
        )},
        *[{"role": m.type, "content": m.content} for m in state["messages"]]
    ]

    # Get LLM response
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    response = await llm.ainvoke(messages)

    # Update state
    state["messages"].append(AIMessage(content=response.content))

    # Try to extract field values from response
    # (Implementation needed for parsing field values from response)

    return state

# Similar implementations needed for:
# - process_optional_fields
# - process_final_confirmation