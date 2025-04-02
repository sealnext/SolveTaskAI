"""
Agent router that handles graph operations.
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.schema.project import Project
from app.schema.api_key import APIKey

from app.agent.thread_manager import get_user_id, message_generator
from app.dependencies import (
    get_db_checkpointer,
    get_ticketing_factory,
    get_thread_repository,
    get_project_service,
    get_api_key_repository,
)
from app.service.ticketing.factory import TicketingClientFactory
from app.repository.thread_repository import ThreadRepository
from app.repository.apikey_repository import APIKeyRepository
from app.service.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/threads")
async def get_threads(
    request: Request, thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> dict:
    """Get all threads for the current user."""
    user_id = get_user_id(request)
    threads = await thread_repo.get_by_user_id(user_id)
    return {"threads": threads, "count": len(threads)}


@router.post("/stream")
async def stream(
    request: Request,
    user_input: dict,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer),
    factory: TicketingClientFactory = Depends(get_ticketing_factory),
    thread_repo: ThreadRepository = Depends(get_thread_repository),
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
) -> StreamingResponse:
    """Stream responses from the agent."""
    user_id = get_user_id(request)
    if not user_input.get("project_id"):
        raise HTTPException(status_code=400, detail="Project ID is required")

    # if the message is empty, check if the "action" is present
    if not (user_input.get("message") or user_input.get("action")):
        raise HTTPException(status_code=400, detail="Message or action is required")

    project: Project = await project_service.get_project_by_id(
        user_id, user_input.get("project_id")
    )
    api_key: APIKey = await api_key_repository.get_api_key_by_user_and_project(
        user_id, project.id
    )
    client = factory.get_client(api_key, project)

    return StreamingResponse(
        message_generator(
            user_input, user_id, project, api_key, checkpointer, thread_repo, client
        ),
        media_type="text/event-stream",
    )


@router.delete("/thread/{thread_id}")
async def delete_thread(
    request: Request,
    thread_id: str,
    thread_repo: ThreadRepository = Depends(get_thread_repository),
) -> dict:
    """Delete a thread and all its associated data."""
    user_id = get_user_id(request)

    if not await thread_repo.verify_ownership(thread_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or you don't have permission to delete it",
        )

    await thread_repo.remove(thread_id)

    return {"status": "success", "message": f"Thread {thread_id} has been deleted"}
