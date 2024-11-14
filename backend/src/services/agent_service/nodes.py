from langgraph.graph import END, MessagesState
from langchain_core.runnables import RunnableConfig
import logging

logger = logging.getLogger(__name__)

async def call_model(state: MessagesState, config: RunnableConfig):
    """Node that calls the LLM with the current state."""
    messages = state["messages"]
    llm = config["configurable"]["llm"]
    
    logger.debug(f"Calling main agent LLM with {len(messages)} messages")
    response = await llm.ainvoke(messages, config)
    
    return {"messages": state["messages"] + [response]}

def should_continue(state: MessagesState):
    """Determine if we should continue with tool calls or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        logger.debug("LLM decided to use tools, returning tools node to route it")
        return "tools"
    
    logger.debug("LLM finished processing, no more tools needed")
    return END 

