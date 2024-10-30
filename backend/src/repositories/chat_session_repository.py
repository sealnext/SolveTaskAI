from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import ChatSession
import logging

logger = logging.getLogger(__name__)

class ChatSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, chat_id: str, user_id: int, project_id: int) -> ChatSession:
        chat_session = ChatSession(
            id=chat_id,
            user_id=user_id,
            project_id=project_id,
            messages=[]  # Initialize with empty list
        )
        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        logger.debug(f"Created new chat session: {chat_id}")
        return chat_session

    async def get_by_id(self, chat_id: str) -> Optional[ChatSession]:
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def add_messages(self, chat_id: str, new_messages: List[dict]) -> ChatSession:
        chat_session = await self.get_by_id(chat_id)
        if chat_session:
            # Convert message objects to dict for JSON storage
            messages_dict = [
                {
                    "type": msg["type"],
                    "content": msg["content"]
                } for msg in new_messages
            ]
            
            # Initialize messages if None
            if chat_session.messages is None:
                chat_session.messages = []
            
            # Add new messages
            chat_session.messages = chat_session.messages + messages_dict
            
            # Explicitly mark as modified
            self.session.add(chat_session)
            await self.session.commit()
            await self.session.refresh(chat_session)
            
            logger.debug(f"Added {len(messages_dict)} messages to chat {chat_id}. Total messages: {len(chat_session.messages)}")
        return chat_session

    async def get_messages(self, chat_id: str) -> List[dict]:
        chat_session = await self.get_by_id(chat_id)
        if chat_session and chat_session.messages:
            logger.debug(f"Retrieved {len(chat_session.messages)} messages from chat {chat_id}")
            return chat_session.messages
        logger.debug(f"No messages found for chat {chat_id}")
        return []