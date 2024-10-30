from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from repositories.chat_session_repository import ChatSessionRepository
import logging

logger = logging.getLogger(__name__)

class ChatMemory:
    def __init__(self, chat_session_repository: ChatSessionRepository):
        self.repository = chat_session_repository

    async def get_chat_history(self, chat_id: str) -> List[dict]:
        """Get chat history for a specific chat ID."""
        messages = await self.repository.get_messages(chat_id)
        logger.debug(f"Retrieved history for {chat_id}: {len(messages)} messages")
        
        # Convert stored messages back to LangChain message objects
        converted_messages = []
        for msg in messages:
            if msg["type"] == "human":
                converted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                converted_messages.append(AIMessage(content=msg["content"]))
            elif msg["type"] == "system":
                converted_messages.append(SystemMessage(content=msg["content"]))
        
        return converted_messages

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