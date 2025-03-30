"""
Message sequence handling and conversation flow management.

This module provides utilities for repairing broken conversation sequences,
handling errors in LLM responses, and formatting responses for the agent system.
It ensures proper conversation flow when tools are interrupted by human input.
"""

import logging
from typing import List, Dict, Any, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks import dispatch_custom_event
from langchain_core.messages import RemoveMessage

logger = logging.getLogger(__name__)


def fix_tool_call_sequence(messages: List[BaseMessage]) -> Dict[str, Any]:
    """
    Detects and fixes a sequence where a tool_call is directly followed by a human message.

    This function ensures proper conversation flow by inserting a missing ToolMessage
    when a human interrupts a tool call.

    Args:
        messages: List of conversation messages

    Returns:
        A dictionary containing:
            - prepared_messages: Messages ready for LLM invocation
            - state_corrections: Commands to fix the state (None if no fix needed)
            - sequence_broken: Boolean indicating if a fix was needed
    """
    # Check if there's a problematic sequence
    sequence_broken = False
    if len(messages) >= 2:
        ai_msg, human_msg = messages[-2], messages[-1]
        # Check if we have a function call followed directly by a human message
        sequence_broken = (
            hasattr(ai_msg, "tool_calls")
            and ai_msg.tool_calls
            and hasattr(human_msg, "type")
            and human_msg.type == "human"
        )

    # Create fixed messages for invoke if needed
    if sequence_broken:
        ai_msg, human_msg = messages[-2], messages[-1]
        tool_call = ai_msg.tool_calls[0]
        tool_id = tool_call["id"]

        # Create the missing ToolMessage
        tool_msg = ToolMessage(
            content="The previous operation was interrupted by user input.",
            tool_call_id=tool_id,
        )

        # Create fixed messages
        prepared_messages = messages[:-1] + [tool_msg, human_msg]

        # Create state fix
        human_id = human_msg.id
        human_content = human_msg.content

        state_corrections = [
            RemoveMessage(id=human_id),
            tool_msg,
            HumanMessage(content=human_content, id=human_id),
        ]
    else:
        prepared_messages = messages
        state_corrections = None

    return {
        "prepared_messages": prepared_messages,
        "state_corrections": state_corrections,
        "sequence_broken": sequence_broken,
    }


def create_error_response(
    error: Exception, state_corrections: Optional[List] = None
) -> Dict[str, List]:
    """
    Creates an appropriate error response when LLM calls fail.

    Args:
        error: The exception that was raised
        state_corrections: Optional state correction commands to apply

    Returns:
        A dictionary containing the messages to return
    """
    logger.error(f"Error calling LLM: {str(error)}")
    error_message = AIMessage(
        content="I'm sorry, I encountered an error. Please try again."
    )

    if state_corrections:
        return {"messages": state_corrections + [error_message]}
    return {"messages": [error_message]}


def format_llm_response(
    response: BaseMessage,
    state_corrections: Optional[List] = None,
    config: Optional[RunnableConfig] = None,
) -> Dict[str, List]:
    """
    Formats the final response from the LLM, handling tool calls and notifications.

    Args:
        response: The response from the LLM
        state_corrections: Optional state correction commands to apply
        config: Optional runnable configuration for event dispatch

    Returns:
        A dictionary containing the messages to return
    """
    # Check for tool calls and dispatch events if necessary
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_name = response.tool_calls[0]["name"]
        if tool_name == "ticket_tool" and config:
            dispatch_custom_event(
                "agent_progress",
                {"message": "We are handling your ticket request..."},
                config=config,
            )

    logger.debug(f"Model response: {response}")

    # Construct final result
    if state_corrections:
        return {"messages": state_corrections + [response]}
    return {"messages": [response]}
