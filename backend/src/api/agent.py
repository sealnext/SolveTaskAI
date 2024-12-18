"""
Agent router that handles graph operations.
"""
import json
import logging
from typing import AsyncGenerator, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.state import AgentState
from agent.graph import create_agent_graph

from agent.utils import (
    convert_message_content_to_string,
    langchain_to_chat_message,
    remove_tool_calls,
)
from dependencies import get_db_checkpointer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["agent"]
)

# TEMPORARY, FOR TESTING PURPOSES
def get_user_id(request: Request) -> str:
    """Extract user ID from request, defaulting to 1 if not found."""
    return request.state.user.id if hasattr(request.state, 'user') and hasattr(request.state.user, 'id') else 1

def create_and_validate_agent(checkpointer: AsyncPostgresSaver) -> AgentState:
    """Create and validate agent graph."""
    agent = create_agent_graph(checkpointer)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active conversations. Please end some before starting new ones."
        )
    return agent

def _parse_input(user_input: dict, user_id: str) -> tuple[dict, dict, UUID]:
    """Parse user input and prepare graph configuration."""
    run_id = uuid4()
    thread_id = user_input.get("thread_id") or str(uuid4())
    
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "checkpoint_ns": "",
        },
        metadata={
            "user_id": user_id,
            "updated_at": str(datetime.now(timezone.utc))
        },
        run_id=run_id
    )
    
    input_state = {
        "messages": [HumanMessage(content=user_input["message"])]
    }
    
    return input_state, config, run_id

@router.post("/invoke")
async def invoke(
    request: Request, 
    user_input: dict,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer)
) -> dict:
    """
    Invoke an agent with user input to retrieve a final response.
    """
    user_id = get_user_id(request)
    agent = create_and_validate_agent(checkpointer)
        
    input_state, config, _ = _parse_input(user_input, user_id)
    response = await agent.ainvoke(input_state, config)
    return dict(langchain_to_chat_message(response["messages"][-1]))

@router.post("/stream")
async def stream(
    request: Request, 
    user_input: dict,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer)
) -> StreamingResponse:
    """Stream responses from the agent."""
    user_id = get_user_id(request)
    
    return StreamingResponse(
        message_generator(user_input, user_id, checkpointer),
        media_type="text/event-stream",
    )

async def message_generator(
    user_input: dict,
    user_id: str,
    checkpointer: AsyncPostgresSaver,
) -> AsyncGenerator[str, None]:
    """Generate a stream of messages from the agent."""
    try:
        agent = create_and_validate_agent(checkpointer)
        input_state, config, _ = _parse_input(user_input, user_id)
        
        async for event in agent.astream_events(input_state, config, version="v2"):
            if not event:
                continue

            new_messages = []
            if (
                event["event"] == "on_chain_end"
                and any(t.startswith("graph:step:") for t in event.get("tags", []))
                and "messages" in event["data"]["output"]
            ):
                new_messages = event["data"]["output"]["messages"]

            if event["event"] == "on_custom_event" and "custom_data_dispatch" in event.get("tags", []):
                new_messages = [event["data"]]

            for message in new_messages:
                try:
                    chat_message = dict(langchain_to_chat_message(message))
                except Exception as e:
                    logger.error(f"Error parsing message: {e}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Unexpected error'})}\n\n"
                    continue
                
                if chat_message["type"] == "human" and chat_message["content"] == user_input["message"]:
                    continue
                    
                yield f"data: {json.dumps({'type': 'message', 'content': chat_message})}\n\n"

            if (
                event["event"] == "on_chat_model_stream"
                and user_input.get("stream_tokens", True)
                and "llama_guard" not in event.get("tags", [])
            ):
                content = remove_tool_calls(event["data"]["chunk"].content)
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': convert_message_content_to_string(content)})}\n\n"

        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in message generator: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': 'Unexpected error'})}\n\n"
        yield "data: [DONE]\n\n"

@router.get("/conversations")
async def list_conversations(
    request: Request,
    checkpointer: AsyncPostgresSaver = Depends(get_db_checkpointer)
) -> list[dict]:
    """List all conversations for the current user."""
    user_id = get_user_id(request)
    
    try:
        config = RunnableConfig(
            configurable={
                "user_id": user_id
            }
        )
        return await checkpointer.alist(config)
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")
  