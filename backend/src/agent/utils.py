"""
Utility functions for agent operations.
"""
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Any
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
    FunctionMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from langgraph.types import Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.graph import create_agent_graph
from typing import AsyncGenerator
import json
import logging
from agent.state import AgentState

from schemas.agent_schema import ChatMessage
from services.ticketing.client import BaseTicketingClient
from repositories.thread_repository import ThreadRepository
from models import Project, APIKey

logger = logging.getLogger(__name__)

def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> Optional[ChatMessage]:
    """Convert a LangChain message to a ChatMessage."""
    if message is None:
        return None
        
    if isinstance(message, HumanMessage):
        return ChatMessage(type="human", content=message.content)
    elif isinstance(message, AIMessage):
        return ChatMessage(type="ai", content=message.content)
    elif isinstance(message, SystemMessage):
        return ChatMessage(type="system", content=message.content)
    elif isinstance(message, FunctionMessage):
        return ChatMessage(type="function", content=message.content)
    elif isinstance(message, ToolMessage):
        return ChatMessage(type="tool", content=message.content)
    elif isinstance(message, tuple):
        # Handle tuple case by extracting the message
        if len(message) > 0 and isinstance(message[0], BaseMessage):
            return langchain_to_chat_message(message[0])
    else:
        raise ValueError(f"Unsupported message type: {message.__class__.__name__}")


def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
    """Remove tool calls from content."""
    if isinstance(content, str):
        return content
    # Currently only Anthropic models stream tool calls, using content item type tool_use.
    return [
        content_item
        for content_item in content
        if isinstance(content_item, str) or content_item["type"] != "tool_use"
    ]


def get_user_id(request: Request) -> str:
    """Temporary function to get user ID from request. Just for testing purposes."""
    return request.state.user.id if hasattr(request.state, 'user') and hasattr(request.state.user, 'id') else 1


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
    thread_id = user_input.get("thread_id", str(uuid4()))
    
    thread = await thread_repo.get(thread_id)
    
    if not thread and user_input.get("thread_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread with id {thread_id} not found"
        )
    elif not thread:
        # Create a new thread-user association
        await thread_repo.create(thread_id, user_id)
    else:
        # Update timestamp for existing thread
        await thread_repo.update_timestamp(thread_id)
    
    configurable = {
        "thread_id": thread_id,
        "checkpoint_ns": "",
    }
    
    config = RunnableConfig(
        configurable=configurable,
        metadata={
            "user_id": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        run_id=run_id
    )

    # Create initial message
    initial_message = HumanMessage(
        content=user_input["message"],
        type="human"
    )
    
    return [initial_message], config, run_id, thread_id

async def message_generator(
    user_input: dict,
    user_id: str,
    project: Project,
    api_key: APIKey,
    checkpointer: AsyncPostgresSaver,
    thread_repo: ThreadRepository,
    ticketing_client: BaseTicketingClient
) -> AsyncGenerator[str, None]:
    try:
        my_message, config, run_id, thread_id = await parse_input(user_input, user_id, checkpointer, thread_repo)
        
        graph = create_agent_graph(checkpointer, ticketing_client)
        yield f"data: {json.dumps({'type': 'init', 'thread_id': str(thread_id)})}\n\n"

        my_message = HumanMessage(content=user_input["message"])
        
        if user_input.get("action") == "continue":
            initial_state = Command(resume={"action": "continue"})
        elif user_input.get("action") == "update":
            initial_state = Command(resume={"action": "update", "data": user_input.get("data")})
        elif user_input.get("action") == "feedback":
            initial_state = Command(resume={"action": "feedback", "data": user_input.get("data")})
        else:
            initial_state = AgentState(
                messages=[my_message],
                project_data={"id": project.id, "name": project.name},
                api_key=api_key
            )
        
        thread = {"configurable": {"thread_id": thread_id}}

        async for event in graph.astream_events(initial_state, thread, version="v2"):
            if not event:
                continue

            if event.get('event') == 'on_chain_stream':
                if '__interrupt__' in event.get('data', {}).get('chunk', {}):
                    interrupt = event['data']['chunk']['__interrupt__'][0]
                    interrupt_data = interrupt.value
                    resumable = interrupt.resumable
                    yield f"data: {json.dumps({'type': 'interrupt', 'resumable': resumable, 'content': interrupt_data})}\n\n"

            elif event.get('event') == 'on_chat_model_stream':
                chunk = event['data']['chunk']
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'stream', 'content': chunk.content})}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error in message generator: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'thread_id': thread_id})}\n\n"