from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .rag.specialized_rag import RetrieveDocuments, create_retrieve_workflow
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
        self.retrieve_workflow = create_retrieve_workflow()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.generator = ResponseGenerator(self.llm)
        self.memory = ChatMemory(chat_session_repository)
        
        # Create the main assistant with retrieve as a tool
        self.assistant_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a specialized ticketing assistant that helps users understand and analyze tickets, issues, "
                "and project documentation from Jira, Confluence, and Azure DevOps. "
                "\n\nYour responsibilities:"
                "\n- For the first question in a chat, always use RetrieveDocuments to build context"
                "\n- For follow-up questions, try to answer using the existing context from the chat history"
                "\n- Only use RetrieveDocuments for follow-ups if you CANNOT answer the question using the existing context"
                "\n- Focus on providing insights about:"
                "\n  * Ticket status and progress"
                "\n  * Project development issues and solutions"
                "\n  * Sprint information and team updates"
                "\n  * Technical documentation and implementation details"
                "\n\nIMPORTANT: Only use RetrieveDocuments if you cannot find the answer in the existing chat history context."
                "\n\nIf the chat history contains relevant information about the current question, DO NOT use RetrieveDocuments."
            ),
            ("human", "Chat History:\n{chat_history}\n\nCurrent Question: {question}\n\nBased on the chat history above, can you answer this question or do you need to retrieve more information?")
        ])
        
        self.assistant = self.assistant_prompt | self.llm.bind_tools([RetrieveDocuments])

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
            # Check if we have any history for this chat
            has_history = await self.memory.has_history(chat_id)
            logger.info(f"Has chat history: {has_history}")
            logger.debug(f"Memory state: {self.memory}")
            
            # Get and format chat history
            chat_history = await self.memory.get_chat_history(chat_id)
            formatted_history = self.memory.format_chat_history(chat_history)
            logger.debug(f"Chat history length: {len(chat_history)}")
            logger.debug(f"Formatted history: {formatted_history[:200]}...")  # First 200 chars for debugging
            
            documents = []
            needs_retrieval = not has_history  # Always retrieve for first message
            
            if has_history:
                # Only ask the assistant if we need more context when we have chat history
                logger.info("Checking if we need more context for follow-up question")
                response = await self.assistant.ainvoke({
                    "question": question,
                    "chat_history": formatted_history
                })
                
                if response.tool_calls:
                    tool_call = response.tool_calls[0]
                    needs_retrieval = tool_call['name'] == "RetrieveDocuments"
                    if needs_retrieval:
                        logger.info("Assistant determined we need more context")
                    else:
                        logger.info("Assistant will use existing context")
                else:
                    logger.info("Assistant will use existing context (no tool calls)")
                    needs_retrieval = False
            
            if needs_retrieval:
                logger.info("Retrieving new documents")
                retrieve_state = {
                    "question": question,
                    "project": self.project,
                    "api_key": self.api_key,
                    "documents": [],
                    "generation": None,
                    "retry_retrieve_count": 0,
                    "ignore_tickets": [],
                    "messages": [],
                    "max_retries": 3,
                    "answers": 0,
                    "loop_step": 0,
                    "tickets": [],
                    "status": "started"
                }
                
                result = await self.retrieve_workflow.ainvoke(retrieve_state)
                logger.info(f"Retrieve workflow result: {result}")
                
                if result and isinstance(result, dict):
                    documents = result.get("documents", [])
            
            # Generate response using documents and chat history
            answer = await self.generator.generate_response(question, documents, formatted_history)
            
            # Add to chat history
            await self.memory.add_to_chat_history(
                chat_id, 
                question, 
                answer, 
                self.generator._format_docs(documents) if documents else None
            )
            
            # Verify that history was updated
            logger.debug(f"After adding to history - Memory state: {self.memory}")
            
            return answer, chat_id
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return (
                "I apologize, but I encountered an error while processing your question. "
                "Please try again or contact support if the issue persists.",
                chat_id
            )