from typing import List, Optional
from langchain_openai import ChatOpenAI
from models import Project
from models.apikey import APIKey
import logging
import uuid
from .generation import ResponseGenerator
from .chat_memory import ChatMemory
from repositories.chat_session_repository import ChatSessionRepository

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, project: Project, api_key: APIKey, chat_session_repository: ChatSessionRepository):
        self.project = project
        self.api_key = api_key
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.generator = ResponseGenerator(self.llm, project=project, api_key=api_key)
        self.memory = ChatMemory(chat_session_repository)

    async def process_question(self, question: str, chat_id: Optional[str] = None) -> tuple[str, str]:
        """Process a question and return the answer along with the chat_id."""
        logger.info(f"Processing question: {question}")
        
        # Generate or use existing chat_id
        if not chat_id:
            chat_id = f"chat_{uuid.uuid4()}"
            logger.info(f"Created new chat session: {chat_id}")
        else:
            logger.info(f"Using existing chat session: {chat_id}")
        
        try:
            # Get chat history
            messages = await self.memory.get_chat_history(chat_id)
            logger.debug(f"Retrieved {len(messages)} messages for processing")
            
            # Generate response and get context if any
            answer, context = await self.generator.generate_response(question, messages)
            
            # Add to chat history with context if available
            await self.memory.add_to_chat_history(chat_id, question, answer, context)
            
            return answer, chat_id
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return (
                "I apologize, but I encountered an error while processing your question. "
                "Please try again or contact support if the issue persists.",
                chat_id
            )