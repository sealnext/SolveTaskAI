import logging
from typing import Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

from config import OPENAI_MODEL
from models import Project
from models.apikey import APIKey
from .tools import create_ticketing_tools
from .prompts import FIELD_COLLECTION_PROMPT
from .conversation_logger import ConversationLogger

logger = logging.getLogger(__name__)
conversation_logger = ConversationLogger()

def should_continue(state: MessagesState):
    """Determine if we should continue with tool calls or end."""
    last_message = state["messages"][-1]
    
    logger.debug(f"Processing message: {last_message}")
    
    # If we have a final response, we're done
    if state.get("final_response"):
        return END
    
    # Track ticket creation progress
    tool_calls = [msg for msg in state["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls]
    tool_names = []
    
    for msg in tool_calls:
        for call in msg.tool_calls:
            if isinstance(call, dict):
                tool_names.append(call.get("name", ""))
            else:
                tool_names.append(call.name)
    
    # If we have tool calls in the last message and it's an AIMessage, continue
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug("Using tools")
        return "tools"
    
    # If we've already got issue types and template, proceed to create ticket
    if "get_issue_types" in tool_names and "get_ticket_template" in tool_names and "create_ticket" not in tool_names:
        logger.debug("Proceeding to create ticket")
        return "tools"  # Return to tools to create the ticket
    
    logger.debug("No more tools needed")
    return END

def create_ticketing_agent(project: Project, api_key: APIKey):
    """Creates a ticketing tool with project and api_key context."""
    
    # Initialize tools
    tools = create_ticketing_tools(project, api_key)
    
    # Initialize LLM with tools but exclude process_ticket_request to prevent recursion
    base_tools = [t for t in tools if t.name != "process_ticket_request"]
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0).bind_tools(base_tools)
    
    async def call_model(state: MessagesState):
        """Process messages through the model."""
        # Log current conversation state
        conversation_logger.log_state(state)
        
        # Add safety check for maximum iterations
        if len(state["messages"]) > 10:  # Increased limit slightly
            state["final_response"] = "Maximum number of iterations reached. Operation cancelled."
            return state
        
        # Check if we already have a final response
        if state.get("final_response"):
            return state
        
        # Track ticket creation progress
        tool_calls = [msg for msg in state["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls]
        tool_names = []
        
        for msg in tool_calls:
            for call in msg.tool_calls:
                if isinstance(call, dict):
                    tool_names.append(call.get("name", ""))
                else:
                    tool_names.append(call.name)
        
        # Prepare context messages
        context_messages = []
        
        # Add context from previous tool calls
        tool_responses = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage) and msg.content:
                tool_responses.append(f"Previous tool response: {msg.content}")
        
        if tool_responses:
            context_messages.append(SystemMessage(content="\n".join(tool_responses)))
        
        # If we have issue types and template but no ticket creation, add guidance
        if "get_issue_types" in tool_names and "get_ticket_template" in tool_names and "create_ticket" not in tool_names:
            context_messages.append(SystemMessage(content="""Now that you have the issue types and template, please create the ticket using create_ticket with these required fields:
            1. issue_type_id: "10010" (for Task)
            2. request: {
                "summary": "Payment Gateway Error - Failed Transactions",
                "description": "Users are experiencing errors during payment processing leading to failed transactions.
                
                Steps to Reproduce:
                1. Select a product
                2. Proceed to checkout
                3. Submit payment details
                4. Error message appears
                
                Expected Behavior:
                - Users should complete transactions without errors
                
                Current Behavior:
                - Error message appears
                - Transactions fail
                - Multiple users affected
                
                Impact:
                - High priority issue affecting business operations
                - Multiple users reporting the problem"
            }"""))
        
        # Add all context messages before invoking LLM
        if context_messages:
            state["messages"].extend(context_messages)
        
        response = await llm.ainvoke(state["messages"])
        logger.debug(f"++++ Invoking model with messages: {state['messages']}")
        state["messages"].append(response)
        
        # If we got a content response, we're done
        if response.content:
            state["final_response"] = response.content
        
        return state
    
    # Create workflow
    workflow = StateGraph(MessagesState)
    
    # Create tool node with base tools only
    tool_node = ToolNode(base_tools)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",    
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    # Compile workflow
    app = workflow.compile()
    
    @tool
    async def process_ticket_request(request: str, ticket_id: Optional[str] = None) -> str:
        """
        Use this tool for doing actions with tickets.
        ALWAYS use this tool for:
        - Creating new tickets
        - Updating existing tickets
        - Any actions that modify tickets
        - What fields are required for a ticket type
        - What ticket types are available to create
        
        Example:
        - "Create a new task for login bug" -> CREATE(request: {"summary": "...", "description": "..."}, issue_type_id: "<id>")
        - "Edit ticket PZ-123 to add label 'urgent'" -> EDIT (ticket_id: PZ-123)
        - "What fields do I need for a task?" -> INFO
        - "What ticket types are available to create?" -> INFO
        """
        logger.info(f"Tool process_ticket_request called with request: {request}")
        
        try:
            # Create initial messages with system context
            messages = [
                SystemMessage(content="""You are a ticket management assistant. Your job is to help users with ticket operations.
                    When creating a ticket, you MUST:
                    1. First get issue types using get_issue_types()
                    2. Then get template using get_ticket_template() with the issue type ID (not name)
                    3. Finally create the ticket with create_ticket() including ALL required fields:
                       - request: {
                           "summary": "The ticket summary",
                           "description": "The ticket description"
                       }
                       - issue_type_id: "The selected issue type ID"
                    
                    When updating a ticket:
                    - Use edit_ticket with the ticket_id and changes
                    
                    When getting information:
                    - Use the appropriate info tool and return the information
                    
                    IMPORTANT: Always use issue type ID (e.g. "10007"), never use the name (e.g. "Task")
                    """),
                HumanMessage(content=(
                    f"Ticket ID: {ticket_id if ticket_id else 'None'}\n"
                    f"Request: {request}\n\n"
                    "Please help me with this ticket operation."
                )),
                AIMessage(content="I'll help you with that ticket operation. Let me check what needs to be done.")
            ]
            
            # Process through workflow
            result = await app.ainvoke({"messages": messages})
            
            # Get the final response
            if result and isinstance(result, dict):
                return result.get("final_response") or result["messages"][-1].content
            return "Failed to process ticket request"
            
        except Exception as e:
            logger.error(f"Error in process_ticket_request: {e}", exc_info=True)
            return f"Error processing ticket request: {str(e)}"
    
    return process_ticket_request