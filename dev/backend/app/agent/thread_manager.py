"""
Conversation and thread management for agent operations.

This module provides utilities for managing conversation threads, parsing user input,
streaming responses, and handling various conversation-related operations for the agent system.
"""

import json
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from langchain_core.messages import (
	HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.schema import CustomStreamEvent, StandardStreamEvent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from app.agent.graph import create_agent_graph
from app.agent.state import AgentState
from app.dto.agent import AgentStreamInput
from app.dto.api_key import ApiKey
from app.dto.project import Project
from app.misc.logger import logger
from app.repository.thread import ThreadRepository
from app.service.ticketing.client import BaseTicketingClient

# Constants for Event Handling (langgraph)
EV_CHAT_MODEL_END = 'on_chat_model_end'
EV_CUSTOM = 'on_custom_event'
EV_CHAIN_STREAM = 'on_chain_stream'
EV_CHAT_MODEL_STREAM = 'on_chat_model_stream'
EV_NAME_AGENT_PROGRESS = 'agent_progress'
META_LANGGRAPH_NODE = 'langgraph_node'
META_CHECKPOINT_NS = 'checkpoint_ns'
NODE_AGENT = 'agent'
KEY_INTERRUPT = '__interrupt__'


async def prepare_conversation_context(
	user_input: AgentStreamInput,
	user_id: int,
	thread_repo: ThreadRepository,
) -> tuple[list[Any], str]:
	"""
	Parse user input, handle thread creation/update, and prepare messages/config.

	Args:
	    user_input: Input from the user (AgentStreamInput model)
	    user_id: User ID
	    thread_repo: Thread repository instance

	Returns:
	    Tuple containing initial messages, configuration, run ID, and thread ID
	"""
	thread_id = user_input.thread_id

	# if thread_id is None, create a new thread else update the existing one
	if thread_id is None:
		thread_id = str(uuid4())
		logger.info(f'Creating new thread: {thread_id}')
		await thread_repo.create(thread_id, user_id, user_input.project_id)
	else:
		thread = await thread_repo.get(thread_id)
		if not thread:
			raise HTTPException(
				status.HTTP_404_NOT_FOUND,
				f'Thread with id {thread_id} not found',
			)
		await thread_repo.update_timestamp(thread_id)

	initial_messages = []
	if user_input.message is not None:
		initial_messages.append(HumanMessage(content=user_input.message, type='human'))

	return initial_messages, thread_id


# --- Helper functions for message_generator ---
def _format_sse(data: dict) -> str:
	"""Formats data as a Server-Sent Event string."""
	return f'data: {json.dumps(data)}\n\n'


def _handle_final_message(
	event: StandardStreamEvent | CustomStreamEvent, thread_id: str
) -> Optional[str]:
	"""Handles 'on_chat_model_end' events from the agent node."""
	metadata = event.get('metadata', {})
	if metadata.get(META_LANGGRAPH_NODE) == NODE_AGENT and metadata.get(
		META_CHECKPOINT_NS, ''
	).startswith(NODE_AGENT):
		final_content = event.get('data', {}).get('output', {}).content
		if final_content:
			return _format_sse(
				{'type': 'final', 'content': final_content, 'thread_id': str(thread_id)}
			)
	return None


def _handle_progress_event(
	event: StandardStreamEvent | CustomStreamEvent, thread_id: str
) -> Optional[str]:
	"""Handles 'agent_progress' custom events."""
	data = event.get('data', {})
	if message := data.get('message'):
		return _format_sse({'type': 'progress', 'content': message, 'thread_id': str(thread_id)})
	return None


def _handle_interrupt_event(
	event: StandardStreamEvent | CustomStreamEvent, thread_id: str
) -> Optional[str]:
	"""
	Handles interrupt events within 'on_chain_stream'.
	Langgraph interrupts are often nested within the 'chunk' tuple: (..., {'__interrupt__': (InterruptObject, ...)})
	"""
	chunk = event.get('data', {}).get('chunk', {})
	if (
		isinstance(chunk, tuple)
		and len(chunk) == 2
		and isinstance(chunk[1], dict)
		and chunk[0] == ()
	):
		interrupt_data = chunk[1].get(KEY_INTERRUPT)
		if (
			isinstance(interrupt_data, tuple)
			and len(interrupt_data) > 0
			and hasattr(interrupt := interrupt_data[0], 'value')
			and hasattr(interrupt, 'resumable')
		):
			return _format_sse(
				{
					'type': 'interrupt',
					'resumable': interrupt.resumable,
					'content': interrupt.value,
					'thread_id': str(thread_id),
				}
			)
	return None


def _handle_stream_event(event: StandardStreamEvent | CustomStreamEvent) -> Optional[str]:
	"""Handles 'on_chat_model_stream' events from the agent node."""
	metadata = event.get('metadata', {})
	if metadata.get(META_LANGGRAPH_NODE) == NODE_AGENT and metadata.get(
		META_CHECKPOINT_NS, ''
	).startswith(NODE_AGENT):
		chunk = event.get('data', {}).get('chunk')
		if chunk and chunk.content:
			return _format_sse({'type': 'stream', 'content': chunk.content})
	return None


async def message_generator(
	user_input: AgentStreamInput,
	user_id: int,
	project: Project,
	api_key: ApiKey,
	checkpointer: AsyncPostgresSaver,
	thread_repo: ThreadRepository,
	ticketing_client: BaseTicketingClient,
) -> AsyncGenerator[str, None]:
	"""Generates Server-Sent Events for the agent's response stream."""
	thread_id = None
	try:
		messages, thread_id = await prepare_conversation_context(user_input, user_id, thread_repo)

		graph = create_agent_graph(checkpointer, ticketing_client)

		# Determine initial state
		if user_input.action == 'confirm':
			initial_state = Command(
				resume={
					'action': 'confirm',
					'payload': user_input.payload,
					'ticket': user_input.ticket,
				}
			)
		elif user_input.action == 'cancel':
			initial_state = Command(resume={'action': 'cancel'})
		else:
			initial_state = AgentState(
				messages=messages,
				project_data={'id': project.id, 'name': project.name},
				api_key=api_key,
			)

		thread_config: RunnableConfig = {'configurable': {'thread_id': thread_id}}

		async for event in graph.astream_events(
			initial_state, thread_config, version='v2', subgraphs=True
		):
			if not event:
				continue

			event_type = event.get('event')
			sse_message = None

			# Dispatch to the appropriate handler based on event type
			if event_type == EV_CHAT_MODEL_END:
				sse_message = _handle_final_message(event, thread_id)
			elif event_type == EV_CUSTOM and event.get('name') == EV_NAME_AGENT_PROGRESS:
				sse_message = _handle_progress_event(event, thread_id)
			elif event_type == EV_CHAIN_STREAM:
				sse_message = _handle_interrupt_event(event, thread_id)
			elif event_type == EV_CHAT_MODEL_STREAM:
				sse_message = _handle_stream_event(event)

			if sse_message:
				yield sse_message

		yield _format_sse({'type': 'done', 'thread_id': str(thread_id)})

	except Exception as e:
		logger.error(f'Error in message generator (Thread ID: {thread_id}): {e}', exc_info=True)
		error_payload = {'type': 'error', 'content': str(e)}
		if thread_id:
			error_payload['thread_id'] = str(thread_id)
		yield _format_sse(error_payload)
