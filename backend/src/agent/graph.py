from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Optional, Literal, Annotated
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from langchain_core.messages import FunctionMessage, ToolMessage
from langgraph.types import Command

from agent.state import AgentState
from agent.configuration import AgentConfiguration
from config.logger import auto_log
from agent.schema import TicketToolInput
import logging
from agent.ticket_tool.graph import create_ticket_graph
from typing import Union, Any

from langchain_core.messages import (
    AnyMessage,
)

logger = logging.getLogger(__name__)

# Create the ticket subgraph once
# ticket_graph = create_ticket_graph()

@tool(args_schema=TicketToolInput)
@auto_log("graph.ticket_tool")
async def ticket_tool(
    action: Literal["edit", "create", "delete"],
    detailed_query: str,
    ticket_id: str,
    config: RunnableConfig,
) -> FunctionMessage:
    """
    Tool for ticket operations using a subgraph implementation.
    
    Args:
        action: Must be one of: "edit", "create", "delete"
        detailed_query: Detailed description of the ticket operation
        ticket_id: The ID of the ticket (required for edit and delete actions)
    """
    return "Mock ticket tool"

@tool
@auto_log("graph.mock_retrieve_tool")
def mock_retrieve_tool(query: str, config: RunnableConfig) -> FunctionMessage:
    """Mock tool that simulates retrieving data from a ticket."""
    return FunctionMessage(content="The weather is 30grade celsius", name="mock_retrieve_tool")

@auto_log("graph.call_model")
async def call_model(state: AgentState, config: RunnableConfig):
    """Node that calls the LLM with the current state."""
    messages = state.messages
    agent_config = AgentConfiguration()
    llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature)
    llm_with_tools = llm.bind_tools([mock_retrieve_tool, ticket_tool])
    
    response = await llm_with_tools.ainvoke(messages)
    
    return {
        "messages": [response]
    }
    
def tools_condition(
    state: Union[list[AnyMessage], dict[str, Any], BaseModel],
) -> Literal["tools", "__end__", "ticket_tool"]:
    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get("messages", [])):
        ai_message = messages[-1]
    elif messages := getattr(state, "messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0 and ai_message.tool_calls[0]['name'] == 'ticket_tool':
        return "ticket_tool"
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"

def create_agent_graph(checkpointer: Optional[AsyncPostgresSaver] = None) -> StateGraph:
    """Create a new agent graph instance."""
    builder = StateGraph(AgentState)
    
    tool_node = ToolNode([mock_retrieve_tool])
    
    # Add nodes
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    builder.add_node("ticket_tool", create_ticket_graph())
    
    # Add edges
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    builder.add_edge("ticket_tool", "agent")
    builder.add_edge("agent", END)
    
    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Graph created successfully: {graph}")
    return graph