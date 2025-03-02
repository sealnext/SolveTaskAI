import logging
from typing import Optional, Literal, Annotated, Any, Coroutine

from app.config.logger import auto_log
from app.services.ticketing.client import BaseTicketingClient

from langchain_core.callbacks import dispatch_custom_event
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from app.agent.ticket_agent.models import TicketAgentState, ReviewAction, ReviewConfig
from app.agent.ticket_agent.utils import (
    handle_review_process,
    prepare_ticket_fields,
    generate_field_updates,
    create_review_config,
    handle_edit_error,
    handle_account_search,
    handle_issue_search,
    handle_sprint_search,
    prepare_creation_fields,
    generate_creation_fields,
)
from app.agent.ticket_agent.prompts import TICKET_AGENT_PROMPT
from app.agent.configuration import AgentConfiguration

logger = logging.getLogger(__name__)


def create_ticket_agent(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    client: BaseTicketingClient = None,
) -> StateGraph:
    """Create a new ticket agent graph instance."""

    @tool(parse_docstring=True)
    async def create_ticket(
        detailed_query: str,
        issue_type: str,
        config: RunnableConfig,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command | Coroutine[Any, Any, Command]:
        """Tool for creating tickets with Jira metadata validation.

        Args:
            detailed_query (str): Each field and its value of the ticket to create.
            issue_type (str): The type of issue to create.
        """
        field_values = {}

        try:
            is_resuming = config.get("configurable", {}).get("__pregel_resuming", False)

            if is_resuming:
                message = await handle_review_process(
                    ReviewConfig(operation_type="create"), client
                )
                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [
                            ToolMessage(content=message, tool_call_id=tool_call_id)
                        ],
                        "done": True,
                    },
                )

            dispatch_custom_event(
                "agent_progress",
                {"message": "Trying to create a new ticket..."},
                config=config,
            )

            # Get project_key from the client's project object
            project_key = client.project.key

            # Get createmeta fields and allowed values
            creation_fields = await prepare_creation_fields(
                project_key, issue_type, client
            )

            # Generate field values using LLM with createmeta constraints
            detailed_query = detailed_query + f"\nProject key: {project_key}"
            field_values = await generate_creation_fields(
                detailed_query, creation_fields
            )

            # Prepare review configuration with createmeta data
            review_config = create_review_config(
                operation_type="create",
                project_key=project_key,
                issue_type=issue_type,
                field_values=field_values,
            )

            message = await handle_review_process(review_config, client)

            return Command(
                goto="agent",
                update={
                    "internal_messages": [
                        ToolMessage(content=message, tool_call_id=tool_call_id)
                    ],
                    "done": True,
                },
            )

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            logger.error(f"Error in create_ticket: {str(e)}", exc_info=True)
            # TODO: return what issue types are available for the project
            # ex : Error in create_ticket: 404: No metadata found for project PZ and issue type issue
            return str(e)

    @auto_log("ticket_agent.edit_ticket")
    async def edit_ticket(
        detailed_query: str,
        ticket_id: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        config: RunnableConfig,
    ) -> Command | Coroutine[Any, Any, Command]:
        """Tool for editing JIRA tickets."""
        try:
            is_resuming = config.get("configurable")["__pregel_resuming"]

            if is_resuming:
                message = await handle_review_process(
                    ReviewConfig(operation_type="edit"), client
                )
                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [
                            ToolMessage(content=message, tool_call_id=tool_call_id)
                        ],
                        "done": True,
                    },
                )

            dispatch_custom_event(
                "agent_progress",
                {
                    "message": f"Mapping changes for ticket {ticket_id}...",
                    "ticket_id": ticket_id,
                },
                config=config,
            )

            # Get metadata and prepare fields
            available_fields = await prepare_ticket_fields(ticket_id, client)

            # Generate field updates using LLM
            field_updates = await generate_field_updates(
                detailed_query, available_fields, config
            )

            # Prepare review configuration
            review_config = create_review_config(
                ticket_id=ticket_id, field_updates=field_updates
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
        config: RunnableConfig,
    ) -> Command | Coroutine[Any, Any, Command]:
        """Tool for deleting tickets with confirmation flow."""
        try:
            is_resuming = config.get("configurable", {}).get("__pregel_resuming", False)

            if is_resuming:
                message = await handle_review_process(
                    ReviewConfig(operation_type="delete"), client
                )
                return Command(
                    goto="agent",
                    update={
                        "internal_messages": [
                            ToolMessage(content=message, tool_call_id=tool_call_id)
                        ],
                        "done": True,
                    },
                )

            # Create review configuration for deletion
            review_config = create_review_config(
                ticket_id=ticket_id,
                operation_type="delete",
                question=f"Confirm permanent deletion of ticket {ticket_id}?",
                available_actions=[ReviewAction.CONFIRM, ReviewAction.CANCEL],
            )

            message = await handle_review_process(review_config, client)
            return ToolMessage(content=message, tool_call_id=tool_call_id)

        except GraphInterrupt as i:
            raise i
        except Exception as e:
            return e

    @tool
    async def search_jira_entity(
        entity_type: Literal["account", "sprint", "issue"], value: str
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
        messages_key="internal_messages",
    )

    async def call_model_with_tools(state: TicketAgentState):
        """Node that calls the LLM with internal message history."""
        agent_config = AgentConfiguration()

        llm = agent_config.get_llm()

        llm_with_tools = llm.bind_tools(
            [create_ticket, edit_ticket, delete_ticket, search_jira_entity]
        )

        if state.done:
            return {
                "messages": [
                    ToolMessage(
                        content=state.internal_messages[-1].content,
                        tool_call_id=state.messages[-1].tool_calls[-1]["id"],
                    )
                ]
            }

        if not state.internal_messages and state.messages[-1].tool_calls:
            args = state.messages[-1].tool_calls[0]["args"]

            # Format the ticket_id section
            ticket_id_section = (
                f"- Ticket ID: {args['ticket_id']}" if args.get("ticket_id") else ""
            )

            # Create the structured prompt using the template
            structured_prompt = TICKET_AGENT_PROMPT.format(
                action=args.get("action", "Not specified"),
                query=args.get("detailed_query", "Not specified"),
                ticket_id_section=ticket_id_section,
            )

            # Always ensure we have at least one valid message with content
            state.internal_messages = [HumanMessage(content=structured_prompt)]

        # Make sure we have at least one message with content for Gemini
        if not state.internal_messages:
            state.internal_messages = [
                HumanMessage(
                    content="Please provide information about the ticket operation."
                )
            ]

        response = await llm_with_tools.ainvoke(state.internal_messages)
        state.internal_messages.append(response)

        if len(response.tool_calls) > 0:
            return Command(
                goto="tools", update={"internal_messages": state.internal_messages}
            )

        return {
            "messages": [
                ToolMessage(
                    content=response.content,
                    tool_call_id=state.messages[-1].tool_calls[0]["id"],
                )
            ]
        }

    builder.add_node("agent", call_model_with_tools)
    builder.add_node("tools", prep_tools)

    builder.set_entry_point("agent")
    builder.add_edge(START, "agent")
    builder.add_edge("tools", "agent")

    graph = builder.compile(checkpointer=checkpointer)
    logger.info(f"Ticket agent graph created successfully: {graph}")
    return graph
