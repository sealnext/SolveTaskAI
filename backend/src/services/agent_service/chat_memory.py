from typing import List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from repositories.chat_session_repository import ChatSessionRepository
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ChatMemory:
    def __init__(self, chat_session_repository: ChatSessionRepository):
        self.repository = chat_session_repository

    def filter_messages(self, messages: List[dict], window_size: int = 4, system_window: int = 3) -> List[dict]:
        """Filter messages to keep only the most recent unique context and system messages.
        
        Args:
            messages: List of messages
            window_size: Number of message pairs to keep (default 4 pairs = last 8 messages)
            system_window: Number of most recent unique system messages to keep (default 3)
        """
        # Separate system messages (context) from conversation messages
        system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
        conversation_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        
        logger.debug(f"Total messages: {len(messages)}, System messages: {len(system_messages)}, "
                    f"Conversation messages: {len(conversation_messages)}")
        
        # Remove duplicates from system messages while preserving order
        unique_system = []
        seen_content = set()
        for msg in reversed(system_messages):  # Process from newest to oldest
            if msg.content not in seen_content:
                unique_system.append(msg)
                seen_content.add(msg.content)
                if len(unique_system) >= system_window:
                    break
        
        # Reverse back to maintain chronological order
        unique_system.reverse()
        
        # Keep last n conversation messages
        filtered_conversation = conversation_messages[-window_size * 2:] if conversation_messages else []
        
        # Combine filtered system messages with filtered conversation
        filtered = unique_system + filtered_conversation
        
        logger.debug(f"Filtered to {len(filtered)} messages: {len(unique_system)} unique system + "
                    f"{len(filtered_conversation)} conversation")
        
        return filtered

    async def get_chat_history(self, chat_id: str) -> List[dict]:
        """Get filtered chat history for a specific chat ID."""
        messages = await self.repository.get_messages(chat_id)
        logger.debug(f"Retrieved history for {chat_id}: {len(messages)} messages")
        
        # Convert stored messages to LangChain message objects
        converted_messages = []
        for msg in messages:
            if msg["type"] == "human":
                converted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                converted_messages.append(AIMessage(content=msg["content"]))
            elif msg["type"] == "system":
                converted_messages.append(SystemMessage(content=msg["content"]))
        
        # Filter messages before returning
        filtered_messages = self.filter_messages(converted_messages)
        logger.debug(f"Returning {len(filtered_messages)} filtered messages")
        return filtered_messages

    async def has_history(self, chat_id: str) -> bool:
        """Check if there is any history for this chat ID."""
        messages = await self.repository.get_messages(chat_id)
        has_history = len(messages) > 0
        logger.debug(f"Chat {chat_id} has history: {has_history}. Messages count: {len(messages)}")
        return has_history

    async def add_to_chat_history(self, chat_id: str, question: str, answer: str, context: Optional[str] = None):
        """Add a Q&A pair to chat history."""
        messages = [
            {"type": "human", "content": question}
        ]
        if context:
            messages.append({"type": "system", "content": f"Context: {context}"})
        messages.append({"type": "ai", "content": answer})
        
        await self.repository.add_messages(chat_id, messages)
        logger.debug(f"Added messages to chat history {chat_id}")

    def format_chat_history(self, messages: List[dict]) -> str:
        """Format chat history for prompt."""
        if not messages:
            logger.debug("No messages to format")
            return ""
        
        formatted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted.append(f"[Context] {msg.content}")
            else:
                role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
                formatted.append(f"{role}: {msg.content}")
        
        formatted_history = "\n".join(formatted)
        logger.debug(f"Formatted {len(messages)} messages into history")
        return formatted_history

    def __str__(self):
        """String representation for debugging."""
        return f"ChatMemory with repository: {self.repository}"