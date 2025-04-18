"""
Conversation and thread management for agent operations.

This module provides utilities for managing conversation threads, parsing user input,
streaming responses, and handling various conversation-related operations for the agent system.
"""

import json
from datetime import datetime, timezone
from logging import getLogger
from typing import AsyncGenerator, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from langchain_core.messages import (
	BaseMessage,
	HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from app.agent.graph import create_agent_graph
from app.agent.state import AgentState
from app.dto.api_key import ApiKey
from app.dto.project import Project
from app.repository.thread import ThreadRepository
from app.service.ticketing.client import BaseTicketingClient

logger = getLogger(__name__)


def get_user_id(request: Request) -> str:
	"""Temporary function to get user ID from request. Just for testing purposes."""
	# TODO: Remove this once we have a proper authentication system
	return (
		request.state.user.id
		if hasattr(request.state, 'user') and hasattr(request.state.user, 'id')
		else 1
	)


async def parse_input(
	user_input: dict,
	user_id: str,
	checkpointer: AsyncPostgresSaver,
	thread_repo: ThreadRepository,
) -> Tuple[list[BaseMessage], RunnableConfig, UUID]:
	"""
	Parse user input and prepare messages and configuration for the graph.

	Args:
	    user_input: Input from the user
	    user_id: User ID
	    checkpointer: AsyncPostgresSaver instance
	    thread_repo: Thread repository instance

	Returns:
	    Tuple containing initial messages, configuration and run ID
	"""
	run_id = uuid4()
	thread_id = user_input.get('thread_id', str(uuid4()))

	thread = await thread_repo.get(thread_id)

	if not thread and user_input.get('thread_id'):
		raise HTTPException(
			status.HTTP_404_NOT_FOUND,
			f'Thread with id {thread_id} not found',
		)
	elif not thread:
		# Create a new thread-user association
		await thread_repo.create(thread_id, user_id)
	else:
		# Update timestamp for existing thread
		await thread_repo.update_timestamp(thread_id)

	configurable = {
		'thread_id': thread_id,
		'checkpoint_ns': '',
	}

	config = RunnableConfig(
		configurable=configurable,
		metadata={
			'user_id': user_id,
			'updated_at': datetime.now(timezone.utc).isoformat(),
		},
		run_id=run_id,
	)

	# Modified message handling
	initial_messages = []
	if 'message' in user_input:
		initial_messages.append(HumanMessage(content=user_input['message'], type='human'))

	return initial_messages, config, run_id, thread_id


async def message_generator(
	user_input: dict,
	user_id: str,
	project: Project,
	api_key: ApiKey,
	checkpointer: AsyncPostgresSaver,
	thread_repo: ThreadRepository,
	ticketing_client: BaseTicketingClient,
) -> AsyncGenerator[str, None]:
	try:
		logger.info('Starting message_generator')

		logger.info('Parsing input...')
		messages, config, run_id, thread_id = await parse_input(
			user_input, user_id, checkpointer, thread_repo
		)
		logger.info(f'Input parsed successfully. Thread ID: {thread_id}')

		graph = create_agent_graph(checkpointer, ticketing_client)

		if user_input.get('action') == 'confirm':
			initial_state = Command(
				resume={
					'action': 'confirm',
					'payload': user_input.get('payload'),
					'ticket': user_input.get('ticket'),
				}
			)
		elif user_input.get('action') == 'cancel':
			initial_state = Command(resume={'action': 'cancel'})
		else:
			initial_state = AgentState(
				messages=messages,
				project_data={'id': project.id, 'name': project.name},
				api_key=api_key,
			)

		thread = {'configurable': {'thread_id': thread_id}}

		async for event in graph.astream_events(
			initial_state, thread, version='v2', subgraphs=True
		):
			if not event:
				continue

			# Handle final stream completed message from agent node
			elif (
				event.get('event') == 'on_chat_model_end'
				and event['metadata']['langgraph_node'] == 'agent'
				and event['metadata']['checkpoint_ns'].startswith('agent')
			):
				final_content = event['data']['output'].content
				if final_content:
					yield f'data: {
						json.dumps(
							{
								"type": "final",
								"content": final_content,
								"thread_id": str(thread_id),
							}
						)
					}\n\n'
				continue

			# Handle custom progress events
			elif event.get('event') == 'on_custom_event' and event.get('name') == 'agent_progress':
				data = event.get('data', {})
				if data and 'message' in data:
					yield f'data: {
						json.dumps(
							{
								"type": "progress",
								"content": data["message"],
								"thread_id": str(thread_id),
							}
						)
					}\n\n'
					continue

			# Handle interrupt events
			elif event.get('event') == 'on_chain_stream':
				chunk = event.get('data', {}).get('chunk', {})
				if isinstance(chunk, tuple) and len(chunk) == 2 and isinstance(chunk[1], dict):
					interrupt_data = chunk[1].get('__interrupt__')
					if (
						interrupt_data
						and isinstance(interrupt_data, tuple)
						and len(interrupt_data) > 0
					):
						interrupt = interrupt_data[0]
						if hasattr(interrupt, 'value') and hasattr(interrupt, 'resumable'):
							yield f'data: {
								json.dumps(
									{
										"type": "interrupt",
										"resumable": interrupt.resumable,
										"content": interrupt.value,
										"thread_id": str(thread_id),
									}
								)
							}\n\n'
							continue

			# Handle stream events from agent node
			elif event.get('event') == 'on_chat_model_stream':
				if event['metadata']['langgraph_node'] == 'agent' and event['metadata'][
					'checkpoint_ns'
				].startswith('agent'):
					chunk = event['data']['chunk']
					if chunk.content:
						yield f'data: {
							json.dumps(
								{
									"type": "stream",
									"content": chunk.content,
								}
							)
						}\n\n'

		yield f'data: {json.dumps({"type": "done", "thread_id": str(thread_id)})}\n\n'

	except Exception as e:
		logger.error(f'Error in message generator: {e}', exc_info=True)
		yield f'data: {
			json.dumps({"type": "error", "content": str(e), "thread_id": str(thread_id)})
		}\n\n'
