# Standard library imports
import logging
from typing import Any, Literal, Optional, Union, Dict, Type, Callable

# Third-party imports
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import dispatch_custom_event
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

# Local application imports
from app.agent.configuration import AgentConfiguration
from app.config.logger import auto_log
from app.services.ticketing.client import BaseTicketingClient

from .prompts import AGENT_SYSTEM_PROMPT
from .state import AgentState
from .ticket_agent.graph import create_ticket_agent

# Logger setup
logger = logging.getLogger(__name__)


@tool
@auto_log("graph.ticket_tool")
async def ticket_tool(
    action: Literal["create", "edit", "delete"], ticket_id: str, detailed_query: str
):
    """Tool for handling complex ticket operations.

    Parameters:
    - action: create, edit, delete, search
    - ticket_id (optional): the id of the ticket to be created, edited or deleted
    - detailed_query: the detailed query to be used for the ticket
    """

    # This tool serves as a declarative interface for the ticket_tool subgraph.
    # While it appears as a standard tool to the LLM, it actually orchestrates
    # a more complex workflow by routing to the dedicated ticket_tool node.
    # The actual implementation is handled by the ticket_tool subgraph, with
    # flow control managed by the tools_condition function which directs
    # tool calls to the appropriate node.

    # We use this approach because LangGraph automatically handles checkpointer propagation
    # to child sub-graphs, eliminating the need for manual implementation. However, LangGraph
    # has limitations when sub-graphs are manually invoked from tools, which is why we need
    # this specific architecture.
    return {}


@auto_log("graph.call_model")
async def call_model(state: AgentState, config: RunnableConfig):
    """Node that calls the LLM with the current state."""
    messages = state.messages
    agent_config = AgentConfiguration()
    llm = agent_config.get_llm()

    llm_with_tools = llm.bind_tools([ticket_tool])
    response = await llm_with_tools.ainvoke(messages)

    if hasattr(response, "tool_calls") and len(response.tool_calls) > 0:
        tool_name = response.tool_calls[0]["name"]
        if tool_name == "ticket_tool":
            dispatch_custom_event(
                "agent_progress",
                {"message": "We are handling your ticket request..."},
                config=config,
            )

    logger.error(f"after llm_with_tools: {response}")
    return {"messages": [response]}


def tools_condition(
    state: Union[list[AnyMessage], dict[str, Any], BaseModel],
) -> Literal["tools", "ticket_tool", "__end__"]:
    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get("messages", [])):
        ai_message = messages[-1]
    elif messages := getattr(state, "messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        tool_name = ai_message.tool_calls[0]["name"]
        if tool_name == "ticket_tool":
            return "ticket_agent"
        return "tools"
    return "__end__"


def create_agent_graph(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    ticketing_client: Optional[BaseTicketingClient] = None,
) -> StateGraph:
    """Create a new agent graph instance."""

    # Create ticket subgraph with client
    ticket_graph = create_ticket_agent(
        checkpointer=checkpointer, client=ticketing_client
    )

    builder = StateGraph(AgentState)

    tool_node = ToolNode([ticket_tool])

    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    builder.add_node("ticket_agent", ticket_graph)

    builder.set_entry_point("agent")
    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", "ticket_agent": "ticket_agent", "__end__": "__end__"},
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("ticket_agent", "agent")

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Graph created successfully: {graph}")
    return graph
