from typing import Dict, Any, TypedDict
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
import logging

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: list
    config: dict

async def call_model(state: AgentState) -> Dict[str, Any]:
    """Node that calls the LLM with the current state.
    
    Args:
        state: Current state containing messages and config
        
    Returns:
        Updated state with new message
    """
    messages = state["messages"]
    config = state.get("config", {})
    llm = config.get("llm")
    
    if not llm:
        logger.error("LLM not found in config")
        raise ValueError("LLM not found in config. Make sure to pass the LLM instance in the config.")
    
    logger.debug(f"Calling LLM with {len(messages)} messages")
    
    response = await llm.ainvoke(messages)
    return {
        "messages": state["messages"] + [response],
        "config": config  # Preserve the config in the state
    }

def should_continue(state: Dict[str, Any]) -> str:
    """Determine if we should continue with tool calls or end.
    
    Args:
        state: Current state containing messages
        
    Returns:
        "tools" if tool calls are needed, "end" otherwise
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug("Tool calls detected, continuing to tools node")
        return "tools"
    
    logger.debug("No tool calls detected, ending workflow")
    return "end"

def create_tool_node(retrieve_tool) -> ToolNode:
    """Create a tool node for document retrieval.
    
    Args:
        retrieve_tool: The document retrieval tool instance
        
    Returns:
        Configured ToolNode instance
    """
    return ToolNode([retrieve_tool.to_tool()])

def extract_final_response(state: Dict[str, Any]) -> tuple[str, str | None]:
    """Extract the final answer and context from the state.
    
    Args:
        state: Final state containing all messages
        
    Returns:
        Tuple of (answer, context)
    """
    messages = state["messages"]
    final_message = messages[-1]
    answer = final_message.content
    
    # Extract context from tool messages if any
    context = None
    tool_messages = [
        msg for msg in messages 
        if hasattr(msg, "tool_call_id") and hasattr(msg, "content")
    ]
    if tool_messages:
        context = tool_messages[-1].content
        
    return answer, context
