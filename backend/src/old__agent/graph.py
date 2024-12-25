from typing import Dict, Any, List, Optional, Sequence
from langchain_core.messages import BaseMessage, AIMessage, AnyMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.documents import Document

import logging
from config.logger import auto_log, log_message
from agent.configuration import AgentConfiguration
from agent.state import AgentState
from .ticketing_tool.agent import create_ticketing_agent
from .rag.agent import create_retrieve_tool
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@auto_log("graph.call_model")
async def call_model(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node that calls the LLM with the current state and specialized tools."""
    try:
        agent_config = AgentConfiguration()
        
        logger.info(f"Message: {state['messages'][-1].content}")
        
        # Get project and api_key from config
        project = config["configurable"].get("project")
        api_key = config["configurable"].get("api_key")
        
        if not project or not api_key:
            raise ValueError("Project and API key must be provided in config")
            
        # Create specialized tools
        tools = [
            create_retrieve_tool(project, api_key),
            create_ticketing_agent(project, api_key),
        ]
        
        # Initialize LLM with tools
        llm = ChatOpenAI(
            model=agent_config.model, 
            temperature=agent_config.temperature
        ).bind_tools(tools)
        
        log_message(
            f"Model: {agent_config.model} | Temp: {agent_config.temperature} | Tools: {len(tools)}", 
            "CONFIG", 
            "graph.call_model"
        )
        
        response = await llm.ainvoke(state["messages"])
        logger.info(f"Response: {response}")
        return {"messages": [*state["messages"], response]}
    
    except Exception as e:
        logger.error(f"Error in call_model: {str(e)}")
        raise RuntimeError(f"Model call failed: {str(e)}")

def create_agent_graph(project, api_key, checkpointer: Optional[AsyncPostgresSaver] = None) -> StateGraph:
    """
    Create an agent graph with specialized tools for retrieval and ticketing.
    
    Args:
        project: Project configuration for tool initialization
        api_key: API key for tool initialization
        checkpointer: Optional PostgreSQL checkpointer for state persistence
        
    Returns:
        Compiled StateGraph instance
    """
    builder = StateGraph(AgentState)
    
    # Create specialized tools
    tools = [
        create_retrieve_tool(project, api_key),
        create_ticketing_agent(project, api_key),
    ]
    
    # Create tool node with specialized tools
    tool_node = ToolNode(tools)
    
    # Add nodes to graph
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    
    # Add edges with conditional routing
    builder.set_entry_point("agent")
    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )
    
    # Connect remaining edges
    builder.add_edge("tools", "agent")
    
    logger.info(f"Creating graph with checkpointer: {checkpointer is not None}")
    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Graph created successfully with {len(tools)} tools")
    
    return graph