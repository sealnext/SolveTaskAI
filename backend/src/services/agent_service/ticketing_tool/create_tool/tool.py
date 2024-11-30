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
        try:
            # Initialize state
            state = TicketCreationState(
                messages=[HumanMessage(content=request)],
                issue_type=None,
                required_fields=None,
                field_values=None
            )
            
            # Process through workflow
            result = await app.ainvoke(state)
            
            # Return final message
            return result["messages"][-1].content
            
        except Exception as e:
            error_msg = f"Failed to process ticket creation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
            
    return create_ticket

async def call_ticket_agent(state: TicketCreationState) -> TicketCreationState:
    """Process messages through the ticket creation agent."""
    messages = [
        {"role": "system", "content": TICKET_CREATION_SYSTEM_MESSAGE},
        *[{"role": m.type, "content": m.content} for m in state["messages"]]
    ]
    
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    response = await llm.ainvoke(messages)
    
    state["messages"].append(AIMessage(content=response.content))
    return state

def should_continue_ticket_creation(state: TicketCreationState) -> str:
    """Determine if we should continue the ticket creation process."""
    last_message = state["messages"][-1].content
    
    if "Successfully created ticket" in last_message:
        return END
        
    if state["issue_type"] is None:
        return "agent"  # Need to select issue type
        
    if state["required_fields"] is None:
        return "agent"  # Need to get required fields
        
    if state["field_values"] is None:
        return "agent"  # Need to collect field values
        
    return END
