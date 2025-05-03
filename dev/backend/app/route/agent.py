"""
Agent router that handles graph operations.
"""

from logging import getLogger
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.thread_manager import message_generator
from app.dependency import (
	ThreadServiceDep,
	get_apikey_service,
	get_db_checkpointer,
	get_project_service,
	get_thread_repository,
	get_ticketing_client_factory,
)
from app.dto.agent import AgentStreamInput
from app.dto.api_key import ApiKey
from app.dto.project import Project
from app.dto.thread import Thread
from app.repository.thread import ThreadRepository
from app.service.apikey import ApiKeyService
from app.service.project import ProjectService
from app.service.ticketing.factory import TicketingClientFactory

logger = getLogger(__name__)

router = APIRouter()


@router.get('/threads', response_model=List[Thread])
async def get_threads(request: Request, thread_service: ThreadServiceDep):
	"""Get all threads for the current user."""
	try:
		threads = await thread_service.get_user_threads(request.state.user_id)
		return threads
	except ValueError as e:
		raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.post('/stream')
async def stream(
	request: Request,
	user_input: AgentStreamInput,
	thread_service: ThreadServiceDep,
	checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer),
	factory: TicketingClientFactory = Depends(get_ticketing_client_factory),
	thread_repo: ThreadRepository = Depends(get_thread_repository),
	project_service: ProjectService = Depends(get_project_service),
	api_key_service: ApiKeyService = Depends(get_apikey_service),
) -> StreamingResponse:
	"""Stream responses from the agent."""
	try:
		user_id = request.state.user_id

		if user_input.project_id is None:
			user_input.project_id = await thread_service.get_project_id(user_input.thread_id)

		project: Project = await project_service.get_project_by_id(user_id, user_input.project_id)
		api_key: ApiKey = await api_key_service.get_api_key_by_project_unmasked(user_id, project.id)
		client = factory.get_client(api_key, project)

		return StreamingResponse(
			message_generator(
				user_input, user_id, project, api_key, checkpointer, thread_repo, client
			),
			media_type='text/event-stream',
		)
	except ValueError as e:
		logger.error(f'Error in stream: {e}')
		raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete('/thread/{thread_id}')
async def delete_thread(
	request: Request,
	thread_id: str,
	thread_service: ThreadServiceDep,
):
	"""Delete a thread and all its associated data."""
	try:
		await thread_service.delete_thread(request.state.user_id, thread_id)
		return {'status': 'success'}
	except ValueError as e:
		raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
