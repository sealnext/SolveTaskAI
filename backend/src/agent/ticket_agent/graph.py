import logging
from typing import Optional, Literal, Annotated, Any, Coroutine

from config.logger import auto_log
from services.ticketing.client import BaseTicketingClient

from langchain_core.callbacks import dispatch_custom_event
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, InjectedState
from langgraph.types import Command

from .models import TicketAgentState, ReviewAction, ReviewConfig
from .utils import handle_review_process, prepare_ticket_fields, generate_field_updates, create_review_config, handle_edit_error, handle_account_search, handle_issue_search, handle_sprint_search
from .prompts import (
    TICKET_AGENT_PROMPT
)
from .. import AgentConfiguration

logger = logging.getLogger(__name__)

def create_ticket_agent(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    client: BaseTicketingClient = None
) -> StateGraph:
    """Create a new ticket agent graph instance."""

    @tool
    @auto_log("ticket_agent.create_ticket")
    async def create_ticket(
        detailed_query: str,
        ticket_id: str,
        action: str,
        config: RunnableConfig,
    ) -> ToolMessage:
        """Tool for creating tickets."""
        dispatch_custom_event(
            "agent_progress",
            {
                "message": f"Creating new ticket {ticket_id}...",
                "ticket_id": ticket_id
            },
            config=config
        )
        tool_call_id = config.get("tool_call_id")
        return ToolMessage(content="Ticket created successfully", tool_call_id=tool_call_id)

    @auto_log("ticket_agent.edit_ticket")
    async def edit_ticket(
        detailed_query: str,
        ticket_id: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[TicketAgentState, InjectedState],
        config: RunnableConfig,
    ) -> Command | Coroutine[Any, Any, Command]:
        """Tool for editing JIRA tickets."""
        try:
            is_resuming = config.get("configurable")['__pregel_resuming']
            
            if is_resuming:
                message = await handle_review_process(ReviewConfig(operation_type="edit"), client)
                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [ToolMessage(content=message, tool_call_id=tool_call_id)],
                        "done": True
                    }
                )

            dispatch_custom_event(
                "agent_progress",
                {"message": f"Mapping changes for ticket {ticket_id}...", "ticket_id": ticket_id},
                config=config
            )

            # Get metadata and prepare fields
            available_fields = await prepare_ticket_fields(ticket_id, client)
            
            # Generate field updates using LLM
            field_updates = await generate_field_updates(
                detailed_query, 
                available_fields, 
                config
            )

            # Prepare review configuration
            review_config = create_review_config(
                ticket_id=ticket_id,
                field_updates=field_updates
            )
            
            message = await handle_review_process(review_config, client)

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            return e

    @tool
    @auto_log("ticket_agent.delete_ticket")
    async def delete_ticket(
        ticket_id: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[TicketAgentState, InjectedState],
        config: RunnableConfig,
    ) -> Command | Coroutine[Any, Any, Command]:
        """Tool for deleting tickets with confirmation flow."""
        try:
            is_resuming = config.get("configurable", {}).get('__pregel_resuming', False)
            
            if is_resuming:
                message = await handle_review_process(ReviewConfig(operation_type="delete"), client)
                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [ToolMessage(content=message, tool_call_id=tool_call_id)],
                        "done": True
                    }
                )

            # Create review configuration for deletion
            review_config = create_review_config(
                ticket_id=ticket_id,
                operation_type="delete",
                question=f"Confirm permanent deletion of ticket {ticket_id}?",
                available_actions=[ReviewAction.CONFIRM, ReviewAction.CANCEL]
            )
            
            message = await handle_review_process(review_config, client)
            return ToolMessage(content=message, tool_call_id=tool_call_id)

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            return e

    @tool
    async def search_jira_entity(
        entity_type: Literal["account", "sprint", "issue"],
        value: str
    ) -> str:
        """
        Search for a Jira entity by specified criteria.

        Parameters:
        - entity_type: account, sprint, issue, epic, project
        - value: the value to search for
        """
        try:
            match entity_type:
                case "account":
                    return await handle_account_search(client, value)
                case "sprint":
                    # TODO: to be optimized
                    return await handle_sprint_search(client, value)
                case "issue":
                    return await handle_issue_search(client, value)
                case _:
                    raise ValueError(f"Unsupported entity type: {entity_type}")

        except Exception as e:
            return f"Search failed: {e}"

    builder = StateGraph(TicketAgentState)

    prep_tools = ToolNode(
        tools=[create_ticket, edit_ticket, delete_ticket, search_jira_entity],
        messages_key="internal_messages"
    )

    async def call_model_with_tools(state: TicketAgentState):
        """Node that calls the LLM with internal message history."""
        llm = ChatOpenAI(model=AgentConfiguration.model, temperature=0)
        llm_with_tools = llm.bind_tools([create_ticket, edit_ticket, delete_ticket, search_jira_entity])

        if state.done:
            return {"messages": [ToolMessage(content=state.internal_messages[-1].content, tool_call_id=state.messages[-1].tool_calls[-1]['id'])]}

        if not state.internal_messages and state.messages[-1].tool_calls:
            args = state.messages[-1].tool_calls[0]['args']

            # Format the ticket_id section
            ticket_id_section = f"- Ticket ID: {args['ticket_id']}" if args.get('ticket_id') else ''

            # Create the structured prompt using the template
            structured_prompt = TICKET_AGENT_PROMPT.format(
                action=args.get('action', 'Not specified'),
                query=args.get('detailed_query', 'Not specified'),
                ticket_id_section=ticket_id_section
            )

            if not state.internal_messages:
                state.internal_messages = [SystemMessage(content=structured_prompt)]
            else:
                # Append the new message while keeping the history
                state.internal_messages.append(SystemMessage(content=structured_prompt))

        response = await llm_with_tools.ainvoke(state.internal_messages)
        state.internal_messages.append(response)

        if len(response.tool_calls) > 0:
            return Command(goto="tools", update={"internal_messages": state.internal_messages})

        return {"messages": [ToolMessage(content=response.content, tool_call_id=state.messages[-1].tool_calls[0]["id"])]}

    builder.add_node("agent", call_model_with_tools)
    builder.add_node("tools", prep_tools)

    builder.set_entry_point("agent")
    builder.add_edge(START, "agent")
    builder.add_edge("tools", "agent")

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph


