import json
from typing import Annotated, Any, Literal

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from app.agent.configuration import AgentConfiguration
from app.agent.ticket_agent.models import ReviewAction, ReviewConfig, TicketAgentState
from app.agent.ticket_agent.prompts import TICKET_AGENT_PROMPT
from app.agent.ticket_agent.utils import (
	create_review_config,
	generate_creation_fields,
	generate_field_updates,
	handle_account_search,
	handle_issue_search,
	handle_review_process,
	handle_sprint_search,
	prepare_creation_fields,
	prepare_ticket_fields,
)
from app.misc.logger import logger
from app.service.ticketing.client import BaseTicketingClient


async def dispatch_tool_progress_event(tool_name: str, config: RunnableConfig):
	"""Dispatch appropriate progress event based on tool name."""
	message_map = {
		'create_ticket': 'Handling your creation request...',
		'edit_ticket': 'Handling your edit request...',
		'delete_ticket': 'Handling your deletion request...',
		'search_jira_entity': 'Searching for the relevant data...',
	}

	message = message_map.get(tool_name, 'Processing your request...')
	await adispatch_custom_event(
		'agent_progress',
		{'message': message},
		config=config,
	)


def create_ticket_agent(
	checkpointer: AsyncPostgresSaver | None = None,
	client: BaseTicketingClient = None,
) -> StateGraph:
	"""Create a new ticket agent graph instance."""

	@tool(parse_docstring=True)
	async def create_ticket(
		detailed_query: str,
		issue_type: str,
		config: RunnableConfig,
		tool_call_id: Annotated[str, InjectedToolCallId],
	) -> str | Command | dict[str, bool | None | Any]:
		"""Tool for creating tickets with Jira metadata validation.

		Args:
		    detailed_query (str): Each field and its value of the ticket to create.
		    issue_type (str): The type of issue to create.
		"""
		try:
			is_resuming = config.get('configurable', {}).get('__pregel_resuming', False)

			if is_resuming:
				message = await handle_review_process(
					ReviewConfig(operation_type='create'), client, config
				)
				# todo don't set done , maybe there is an error
				return Command(
					goto='agent',
					update={
						'internal_messages': [
							ToolMessage(content=message, tool_call_id=tool_call_id)
						],
						'done': True,
					},
				)
			# Get project_key from the client's project object
			project_key = client.project.key

			# Get createmeta fields and allowed values
			creation_fields = await prepare_creation_fields(project_key, issue_type, client)

			# Generate field values using LLM with createmeta constraints
			detailed_query = (
				detailed_query + f'\nProject key: {project_key} \nIssue type: {issue_type}'
			)
			field_values = await generate_creation_fields(detailed_query, creation_fields, config)

			if field_values.get('error'):
				return Command(
					goto='agent',
					update={
						'internal_messages': [
							ToolMessage(
								content=field_values.get('error'), tool_call_id=tool_call_id
							)
						],
						'done': True,
					},
				)

			# Prepare review configuration with createmeta data
			review_config = create_review_config(
				operation_type='create',
				project_key=project_key,
				issue_type=issue_type,
				field_values=field_values,
			)

			message = await handle_review_process(review_config, client, config)

			return Command(
				goto='agent',
				update={
					'internal_messages': [ToolMessage(content=message, tool_call_id=tool_call_id)],
					'done': True,
				},
			)

		except GraphInterrupt as i:
			raise i
		except Exception as e:
			logger.exception('Error in create_ticket: %s', e)
			return f'Failure - {e}'

	async def edit_ticket(
		detailed_query: str,
		ticket_id: str,
		config: RunnableConfig,
		tool_call_id: Annotated[str, InjectedToolCallId],
	) -> Command:
		"""Tool for editing tickets

		Args:
		    detailed_query (str): Each field and its value to edit
		    ticket_id (str): The issue id you want to edit
		"""
		try:
			is_resuming = config.get('configurable')['__pregel_resuming']

			if is_resuming:
				message = await handle_review_process(
					ReviewConfig(operation_type='edit'), client, config
				)
				return Command(
					goto='agent',
					update={
						'internal_messages': [
							ToolMessage(content=message, tool_call_id=tool_call_id)
						],
						'done': True,
					},
				)
			# Get metadata and prepare fields
			available_fields = await prepare_ticket_fields(ticket_id, client)

			# Generate field updates using LLM
			field_updates = await generate_field_updates(detailed_query, available_fields, config)

			# Prepare review configuration
			review_config = create_review_config(
				ticket_id=ticket_id, field_updates=field_updates, operation_type='edit'
			)

			message = await handle_review_process(review_config, client, config)

		except GraphInterrupt as i:
			raise i
		except Exception as e:
			return e

	@tool
	async def delete_ticket(
		ticket_id: str,
		tool_call_id: Annotated[str, InjectedToolCallId],
		config: RunnableConfig,
	) -> Command:
		"""Tool for deleting tickets with confirmation flow."""
		try:
			is_resuming = config.get('configurable', {}).get('__pregel_resuming', False)

			if is_resuming:
				message = await handle_review_process(
					ReviewConfig(operation_type='delete'), client, config
				)
				return Command(
					goto='agent',
					update={
						'internal_messages': [
							ToolMessage(content=message, tool_call_id=tool_call_id)
						],
						'done': True,
					},
				)

			# Create review configuration for deletion
			review_config = create_review_config(
				ticket_id=ticket_id,
				operation_type='delete',
				question=f'Confirm permanent deletion of ticket {ticket_id}?',
				available_actions=[ReviewAction.CONFIRM, ReviewAction.CANCEL],
			)

			message = await handle_review_process(review_config, client, config)
			return ToolMessage(content=message, tool_call_id=tool_call_id)

		except GraphInterrupt as i:
			raise i
		except Exception as e:
			return e

	@tool
	async def search_jira_entity(
		entity_type: Literal['account', 'sprint', 'issue'], value: str
	) -> str:
		"""
		Search for a Jira entity by specified criteria.

		Parameters:
		- entity_type: account, sprint, issue, epic, project
		- value: the value to search for
		"""
		try:
			if entity_type == 'account':
				return await handle_account_search(client, value)

			if entity_type == 'sprint':
				# TODO: to be optimized
				return await handle_sprint_search(client, value)

			if entity_type == 'issue':
				return await handle_issue_search(client, value)

		except Exception as e:
			return f'Search failed: {e}'

	builder = StateGraph(TicketAgentState)

	prep_tools = ToolNode(
		tools=[create_ticket, edit_ticket, delete_ticket, search_jira_entity],
		messages_key='internal_messages',
	)

	async def call_model_with_tools(state: TicketAgentState, config: RunnableConfig):
		"""Node that calls the LLM with internal message history."""
		agent_config = AgentConfiguration()
		checkpointer = config['configurable']['__pregel_checkpointer']
		llm = agent_config.get_llm(checkpointer=checkpointer)
		llm_with_tools = llm.bind_tools(
			[create_ticket, edit_ticket, delete_ticket, search_jira_entity]
		)

		if state.done:
			return _create_final_response(state)

		if not state.internal_messages:
			await _prepare_initial_messages(state)

		response = await llm_with_tools.ainvoke(state.internal_messages)
		state.internal_messages.append(response)

		if len(response.tool_calls) > 0:
			tool_name = response.tool_calls[0]['name']
			await dispatch_tool_progress_event(tool_name, config)

			return Command(goto='tools', update={'internal_messages': state.internal_messages})

		return _create_tool_message_response(state)

	def _create_final_response(state: TicketAgentState):
		"""Create the final response when state is done."""
		return {
			'messages': [
				ToolMessage(
					content=state.internal_messages[-1].content,
					tool_call_id=state.messages[-1].tool_calls[-1]['id'],
				)
			]
		}

	async def _prepare_initial_messages(state: TicketAgentState):
		"""Prepare initial messages if none exist."""
		if len(state.context_metadata) == 0:
			state.context_metadata = await client.get_project_context()

		if state.messages[-1].tool_calls:
			args = state.messages[-1].tool_calls[0]['args']
			ticket_id_section = f'- Ticket ID: {args["ticket_id"]}' if args.get('ticket_id') else ''

			structured_prompt = TICKET_AGENT_PROMPT.format(
				action=args.get('action', 'Not specified'),
				query=args.get('detailed_query', 'Not specified'),
				ticket_id_section=ticket_id_section,
				context=json.dumps(state.context_metadata, indent=1),
			)

			state.internal_messages = [HumanMessage(content=structured_prompt)]
		else:
			state.internal_messages = [
				HumanMessage(content='Please provide information about the ticket operation.')
			]

	def _create_tool_message_response(state: TicketAgentState):
		"""Create a tool message response from the current state."""
		return {
			'messages': [
				ToolMessage(
					content=state.internal_messages[-1].content,
					tool_call_id=state.messages[-1].tool_calls[0]['id'],
				)
			]
		}

	builder.add_node('agent', call_model_with_tools)
	builder.add_node('tools', prep_tools)

	builder.set_entry_point('agent')
	builder.add_edge(START, 'agent')
	builder.add_edge('tools', 'agent')

	graph = builder.compile(checkpointer=checkpointer)
	logger.info('Ticket agent graph created successfully: %s', graph)
	return graph
