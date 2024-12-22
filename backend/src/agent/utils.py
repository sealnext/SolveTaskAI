"""
Utility functions for agent operations.
"""
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from typing import AsyncGenerator
import json
import logging

from schemas.agent_schema import ChatMessage
from agent.state import AgentState
from agent.graph import create_agent_graph
from repositories.thread_repository import ThreadRepository

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


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Create a ChatMessage from a LangChain message."""
    match message:
        case HumanMessage():
            human_message = ChatMessage(
                type="human",
                content=convert_message_content_to_string(message.content),
            )
            return human_message
        case AIMessage():
            ai_message = ChatMessage(
                type="ai",
                content=convert_message_content_to_string(message.content),
            )
            if message.tool_calls:
                ai_message.tool_calls = message.tool_calls
            if message.response_metadata:
                ai_message.response_metadata = message.response_metadata
            return ai_message
        case ToolMessage():
            tool_message = ChatMessage(
                type="tool",
                content=convert_message_content_to_string(message.content),
                tool_call_id=message.tool_call_id,
            )
            return tool_message
        case LangchainChatMessage():
            if message.role == "custom":
                custom_message = ChatMessage(
                    type="custom",
                    content="",
                    custom_data=message.content[0],
                )
                return custom_message
            else:
                raise ValueError(f"Unsupported chat message role: {message.role}")
        case _:
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


def create_and_validate_agent(checkpointer: AsyncPostgresSaver) -> AgentState:
    """Create and validate agent graph."""
    agent = create_agent_graph(checkpointer)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active conversations. Please end some before starting new ones."
        )
    return agent


async def create_initial_checkpoint(
    thread_id: str,
    user_id: str,
    checkpointer: AsyncPostgresSaver
) -> None:
    """
    Create an initial checkpoint for a new thread.
    
    Args:
        thread_id: Thread ID
        user_id: User ID
        checkpointer: AsyncPostgresSaver instance
    """
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "checkpoint_ns": "",
        }
    )
    
    checkpoint = Checkpoint(
        v=1,
        id=thread_id,
        ts=datetime.now(timezone.utc).isoformat(),
        channel_values={},
        channel_versions={},
        versions_seen={},
        pending_sends=[]
    )
    
    metadata = CheckpointMetadata(
        source="initial",
        step=0,
        writes=[],
        parents=[],
        user_id=user_id,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    # await checkpointer.aput(
    #     config=config,
    #     checkpoint=checkpoint,
    #     metadata=metadata,
    #     new_versions={}
    # )


async def parse_input(
    user_input: dict,
    user_id: str,
    checkpointer: AsyncPostgresSaver,
    thread_repo: ThreadRepository
) -> Tuple[Dict, RunnableConfig, UUID]:
    """
    Parse user input and prepare configuration for the graph.
    
    Args:
        user_input: Input from the user
        user_id: User ID
        checkpointer: AsyncPostgresSaver instance
        thread_repo: Thread repository instance
        
    Returns:
        Tuple containing initial state, configuration and run ID
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
    
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "checkpoint_ns": "",
        },
        metadata={
            "user_id": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        run_id=run_id
    )
    
    # Let langgraph handle the message state
    input_state = {
        "messages": [HumanMessage(content=user_input["message"])]
    }
    
    return input_state, config, run_id

async def message_generator(
    user_input: dict,
    user_id: str,
    checkpointer: AsyncPostgresSaver,
    thread_repo: ThreadRepository
) -> AsyncGenerator[str, None]:
    """Generate a stream of messages from the agent."""
    try:
        agent = create_and_validate_agent(checkpointer)
        input_state, config, _ = await parse_input(user_input, user_id, checkpointer, thread_repo)
        thread_id = config["configurable"]["thread_id"]
        
        # Send initial message with thread_id
        yield f"data: {json.dumps({'type': 'init', 'thread_id': thread_id})}\n\n"
        
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
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Unexpected error', 'thread_id': thread_id})}\n\n"
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

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in message generator: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': 'Unexpected error', 'thread_id': thread_id})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"
  