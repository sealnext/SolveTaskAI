"""
Agent router that handles graph operations.
"""

from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.thread_manager import get_user_id, message_generator
from app.dependency import (
	get_apikey_service,
	get_db_checkpointer,
	get_project_service,
	get_thread_repository,
	get_ticketing_client_factory,
)
from app.dto.agent import AgentStreamInput
from app.dto.api_key import ApiKey
from app.dto.project import Project
from app.service.apikey import ApiKeyService
from app.repository.thread import ThreadRepository
from app.service.project import ProjectService
from app.service.ticketing.factory import TicketingClientFactory

logger = getLogger(__name__)

router = APIRouter(prefix='/agent', tags=['agent'])


@router.get('/threads')
async def get_threads(
	request: Request, thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> dict:
	"""Get all threads for the current user."""
	# TODO Add pagination
	threads = await thread_repo.get_by_user_id(request.state.user_id)
	return {'threads': threads, 'count': len(threads)}


@router.post('/stream')
async def stream(
	request: Request,
	user_input: AgentStreamInput,
	checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer),
	factory: TicketingClientFactory = Depends(get_ticketing_client_factory),
	thread_repo: ThreadRepository = Depends(get_thread_repository),
	project_service: ProjectService = Depends(get_project_service),
	api_key_service: ApiKeyService = Depends(get_apikey_service),
) -> StreamingResponse:
	"""Stream responses from the agent."""
	user_id = request.state.user_id

	project: Project = await project_service.get_project_by_id(user_id, user_input.project_id)
	api_key: ApiKey = await api_key_service.get_api_key_by_project_unmasked(user_id, project.id)
	client = factory.get_client(api_key, project)

	return StreamingResponse(
		message_generator(user_input, user_id, project, api_key, checkpointer, thread_repo, client),
		media_type='text/event-stream',
	)


@router.delete('/thread/{thread_id}')
async def delete_thread(
	request: Request,
	thread_id: str,
	thread_repo: ThreadRepository = Depends(get_thread_repository),
) -> dict:
	"""Delete a thread and all its associated data."""
	if not await thread_repo.verify_ownership(thread_id, request.state.user_id):
		raise HTTPException(
			status.HTTP_404_NOT_FOUND,
			detail='Thread not found',
		)

	await thread_repo.remove(thread_id)

	return {'status': 'success'}
