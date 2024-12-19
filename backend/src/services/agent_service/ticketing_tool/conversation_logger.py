import logging
from typing import Any, Dict, Set
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

class ConversationLogger:
    def __init__(self):
        self.logger = logging.getLogger("conversation")
        self.logger.setLevel(logging.INFO)
        self.seen_messages = set()  # Track seen messages to avoid duplicates

        # Create console handler with custom formatting
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')  # Simplified format
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _format_tool_call(self, message: AIMessage) -> str:
        """Format a tool call message."""
        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            return ""

        tool_calls = []
        for call in message.tool_calls:
            if isinstance(call, dict):
                name = call.get('name', 'unknown')
                args = call.get('args', '{}')
                tool_calls.append(f"{name}({args})")
            else:
                tool_calls.append(f"{call.name}({call.args})")
        return f"Tool called: {', '.join(tool_calls)}"

    def _format_tool_response(self, message: ToolMessage) -> str:
        """Format a tool response message."""
        if not message.content:
            return ""
        return f"Tool response: {message.content}"

    def _get_message_id(self, message: BaseMessage) -> str:
        """Generate a unique ID for a message to avoid duplicates."""
        if hasattr(message, 'tool_calls'):
            return str(message.tool_calls)
        return str(message.content)

    def log_state(self, state: Dict[str, Any]) -> None:
        """Log only tool calls and their responses."""
        if "messages" not in state:
            return

        messages = state["messages"]
        for i, message in enumerate(messages):
            msg_id = self._get_message_id(message)
            if msg_id in self.seen_messages:
                continue

            self.seen_messages.add(msg_id)

            # Only process AIMessage with tool calls and their ToolMessage responses
            if isinstance(message, AIMessage) and hasattr(message, 'tool_calls') and message.tool_calls:
                tool_call = self._format_tool_call(message)
                if tool_call:
                    self.logger.info(tool_call)

                # Look for the tool response in the next message
                if i + 1 < len(messages) and isinstance(messages[i + 1], ToolMessage):
                    tool_response = self._format_tool_response(messages[i + 1])
                    if tool_response:
                        self.logger.info(tool_response)

        if "final_response" in state and str(state["final_response"]) not in self.seen_messages:
            self.seen_messages.add(str(state["final_response"]))
            self.logger.info(f"Final: {state['final_response']}")