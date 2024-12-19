from typing import Dict, Any, List, Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


from config import OPENAI_MODEL
from models import Project, APIKey
from .prompts import TICKET_CREATION_SYSTEM_MESSAGE

class TicketCreationState(TypedDict):
    """State for the ticket creation workflow."""
    messages: List[BaseMessage]
    issue_type: Optional[str]
    required_fields: Optional[Dict[str, Any]]
    field_values: Optional[Dict[str, Any]]

def create_create_ticketing_tool(project: Project, api_key: APIKey):
    """Creates a ticket creation sub-agent with its own workflow."""

    # Initialize tools
    tools = [
        get_issue_types_tool(project, api_key),
        get_required_fields_tool(project, api_key),
        create_ticket_tool(project, api_key)
    ]

    # Create workflow
    workflow = StateGraph(TicketCreationState)

    # Add nodes
    workflow.add_node("agent", call_ticket_agent)
    workflow.add_node("tools", ToolNode(tools))

    # Add edges
    workflow.add_edge("agent", "tools")
    workflow.add_conditional_edges(
        "tools",
        should_continue_ticket_creation,
        {
            "agent": "agent",
            END: END
        }
    )

    # Compile workflow
    app = workflow.compile()

    @tool("create_ticket", return_direct=True)
    async def create_ticket(request: str) -> str:
        """
        Tool for ticket creation process. Handles the entire flow from selecting
        issue type to creating the ticket with all required fields.

        Use this tool when:
        - User wants to create a new ticket
        - User wants to know what fields are needed

        Do NOT use this tool for:
        - Searching existing tickets
        - Editing existing tickets
        """
        logger.info(f"[CREATE TOOL] Starting ticket creation with request: {request}")
        try:
            # Initialize state
            state = TicketCreationState(
                messages=[HumanMessage(content=request)],
                issue_type=None,
                required_fields=None,
                field_values=None
            )
            logger.debug(f"[CREATE TOOL] Initial state: {state}")

            # Process through workflow
            result = await app.ainvoke(state)
            logger.info(f"[CREATE TOOL] Workflow result: {result}")

            # Return final message
            final_message = result["messages"][-1].content
            logger.info(f"[CREATE TOOL] Final response: {final_message}")
            return final_message

        except Exception as e:
            error_msg = f"Failed to process ticket creation: {str(e)}"
            logger.error(f"[CREATE TOOL] {error_msg}", exc_info=True)
            return error_msg

    return create_ticket

async def call_ticket_agent(state: TicketCreationState) -> TicketCreationState:
    """Process messages through the ticket creation agent."""
    logger.info("[CREATE TOOL] Calling ticket agent")
    messages = [
        {"role": "system", "content": TICKET_CREATION_SYSTEM_MESSAGE},
        *[{"role": m.type, "content": m.content} for m in state["messages"]]
    ]
    logger.debug(f"[CREATE TOOL] Messages for LLM: {messages}")

    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    response = await llm.ainvoke(messages)
    logger.debug(f"[CREATE TOOL] LLM response: {response.content}")

    state["messages"].append(AIMessage(content=response.content))
    return state

def should_continue_ticket_creation(state: TicketCreationState) -> str:
    """Determine if we should continue the ticket creation process."""
    last_message = state["messages"][-1].content
    logger.debug(f"[CREATE TOOL] Checking continuation. Last message: {last_message}")

    if "Successfully created ticket" in last_message:
        logger.info("[CREATE TOOL] Ticket creation completed successfully")
        return END

    if state["issue_type"] is None:
        logger.debug("[CREATE TOOL] Need to select issue type")
        return "agent"

    if state["required_fields"] is None:
        logger.debug("[CREATE TOOL] Need to get required fields")
        return "agent"

    if state["field_values"] is None:
        logger.debug("[CREATE TOOL] Need to collect field values")
        return "agent"

    logger.info("[CREATE TOOL] All requirements met, ending workflow")
    return END

@tool("edit_ticket")
async def edit_ticket(ticket_id: str, changes: str) -> str:
    """
    Edit an existing ticket with the specified changes.
    Use this when you need to modify an existing ticket.

    Args:
        ticket_id: The ID of the ticket to edit (e.g., 'KAN-123')
        changes: Description of changes to make (e.g., "Set epic parent to KAN-8")
    """
    logger.info(f"[EDIT TOOL] Starting edit for ticket {ticket_id} with changes: {changes}")

    try:
        # Parse epic parent from changes
        if "epic parent" in changes.lower():
            epic_key = None
            # Extract epic key from changes text
            import re
            match = re.search(r'(?i)(?:to|as|=)\s*([A-Z]+-\d+)', changes)
            if match:
                epic_key = match.group(1).upper()
                logger.info(f"[EDIT TOOL] Extracted epic key: {epic_key}")

            if not epic_key:
                error = "Could not extract epic key from changes"
                logger.error(f"[EDIT TOOL] {error}")
                return f"Failed to update ticket: {error}"

            # Call Jira client with epic parent update
            result = await jira_client.edit_ticket(ticket_id, {
                "changes": changes,
                "epic_key": epic_key
            })

            logger.info(f"[EDIT TOOL] Edit result: {result}")

            if result.get("success"):
                return f"Successfully updated ticket {ticket_id}"
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"[EDIT TOOL] Failed to update ticket: {error}")
                return f"Failed to update ticket: {error}"

        return f"Unsupported change requested: {changes}"

    except Exception as e:
        error_msg = f"Error updating ticket {ticket_id}: {str(e)}"
        logger.error(f"[EDIT TOOL] {error_msg}", exc_info=True)
        return error_msg
