from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from langchain_core.messages import FunctionMessage

# should be a project schema, as we dont want to expose an entire the project model to the agent
from models import Project
from schemas import APIKeySchema

from agent.state import AgentState
from agent.configuration import AgentConfiguration
from config.logger import auto_log, log_message
import logging

logger = logging.getLogger(__name__)

@tool
@auto_log("graph.mock_retrieve_tool")
def mock_retrieve_tool(query: str, config: RunnableConfig) -> FunctionMessage:
    """
        Use this tool for searching and retrieving information from tickets and documentation.
        ALWAYS use this tool for:
        - Finding information about bugs, issues, or features
        - Searching through ticket content
        - Getting context about specific topics
        - Answering questions about existing tickets
        - Finding how many tickets match certain criteria
        
        Do NOT use this tool for:
        - Creating new tickets
        - Updating existing tickets
        - Any actions that modify tickets
        - Questions about ability to modify tickets
        
        Args:
            query: The search query to use for document retrieval
        
        Returns:
            FunctionMessage containing the retrieved documents or empty if none found
        """
    logger.info(f"Mock retrieve tool called with query: {query}")
    return FunctionMessage(content="The weather is 30grade celsius", name="mock_retrieve_tool")

@auto_log("graph.call_model")
async def call_model(state: AgentState, config: RunnableConfig):
    """Node that calls the LLM with the current state."""
    messages = state.messages
    agent_config = AgentConfiguration()
    llm = ChatOpenAI(model=agent_config.model, temperature=agent_config.temperature)
    llm_with_tools = llm.bind_tools([mock_retrieve_tool])
    
    response = await llm_with_tools.ainvoke(messages)
    
    return {
        "messages": [response]
    }

def create_agent_graph(checkpointer: Optional[AsyncPostgresSaver] = None) -> StateGraph:
    """Create a new agent graph instance."""
    builder = StateGraph(AgentState)
    
    tool_node = ToolNode([mock_retrieve_tool])
    
    # Add nodes
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    
    # Add edges
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    builder.add_edge("agent", END)
    
    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Graph created successfully: {graph}")
    return graph