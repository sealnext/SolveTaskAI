"""
Agent router that handles graph operations.
"""
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.utils import (
    langchain_to_chat_message,
    get_user_id,
    create_and_validate_agent,
    parse_input,
    message_generator
)
from dependencies import get_db_checkpointer, get_thread_repository
from middleware import auth_middleware
from repositories.thread_repository import ThreadRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    # dependencies=[Depends(auth_middleware)]
)

@router.get("/threads")
async def get_threads(
    request: Request,
    thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> dict:
    """Get all threads for the current user."""
    user_id = get_user_id(request)
    threads = await thread_repo.get_by_user_id(user_id)
    return {
        "threads": threads,
        "count": len(threads)
    }

@router.post("/invoke")
async def invoke(
    request: Request, 
    user_input: dict,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> dict:
    """Invoke an agent with user input to retrieve a final response."""
    user_id = get_user_id(request)
    agent = create_and_validate_agent(checkpointer)
        
    input_state, config, _ = await parse_input(user_input, user_id, checkpointer, thread_repo)
    response = await agent.ainvoke(input_state, config)
    
    # Include thread_id in response
    thread_id = config["configurable"]["thread_id"]
    message = dict(langchain_to_chat_message(response["messages"][-1]))
    return {
        "message": message,
        "thread_id": thread_id
    }

@router.post("/stream")
async def stream(
    request: Request, 
    user_input: dict,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> StreamingResponse:
    """Stream responses from the agent."""
    user_id = get_user_id(request)
    
    return StreamingResponse(
        message_generator(user_input, user_id, checkpointer, thread_repo),
        media_type="text/event-stream",
    )

@router.delete("/thread/{thread_id}")
async def delete_thread(
    request: Request,
    thread_id: str,
    thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> dict:
    """Delete a thread and all its associated data."""
    user_id = get_user_id(request)
    
    if not await thread_repo.verify_ownership(thread_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or you don't have permission to delete it"
        )
    
    await thread_repo.remove(thread_id)
    
    return {"status": "success", "message": f"Thread {thread_id} has been deleted"}