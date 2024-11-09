from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
import logging
import uuid
from .rag.specialized_rag import RetrieveDocuments
from models import Project
from models.apikey import APIKey
from repositories.chat_session_repository import ChatSessionRepository
from .chat_memory import ChatMemory
from .nodes import call_model, should_continue, create_tool_node, extract_final_response
from config import OPENAI_MODEL

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, project: Project, api_key: APIKey, chat_session_repository: ChatSessionRepository):
        self.project = project
        self.api_key = api_key
        self.chat_session_repository = chat_session_repository
        self.memory = ChatMemory(chat_session_repository)
        
        # Initialize tools and LLM
        self.retrieve_tool = RetrieveDocuments(project=project, api_key=api_key)
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        self.llm_with_tools = self.llm.bind_tools(
            [self.retrieve_tool.to_tool()],
            tool_choice="auto"
        )
        
        # Initialize the workflow graph with config
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()

    def _create_workflow(self) -> StateGraph:
        """Create the ReAct agent workflow."""
        workflow = StateGraph(MessagesState)
        
        # Create a configured call_model node with the LLM
        async def configured_call_model(state):
            state["config"] = {"llm": self.llm_with_tools}
            return await call_model(state)
        
        # Add nodes
        workflow.add_node("agent", configured_call_model)
        workflow.add_node("tools", create_tool_node(self.retrieve_tool))
        
        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent", 
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow

    async def process_question(self, question: str, chat_id: Optional[str] = None) -> tuple[str, str]:
        """Process a question using the ReAct agent workflow."""
        logger.info(f"Processing question: {question}")
        
        if not chat_id:
            chat_id = f"chat_{uuid.uuid4()}"
            logger.info(f"Created new chat session: {chat_id}")
        
        try:
            # Get chat history
            messages = await self.memory.get_chat_history(chat_id)
            
            # Add the new question
            messages.append(HumanMessage(content=question))
            
            # Run the workflow
            result = await self.app.ainvoke({
                "messages": messages,
                "config": {"llm": self.llm_with_tools}  # Initial config
            })
            
            # Extract the final answer and context
            answer, context = extract_final_response(result)
            
            # Save to chat history
            await self.memory.add_to_chat_history(chat_id, question, answer, context)
            
            return answer, chat_id
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return (
                "I apologize, but I encountered an error while processing your question. "
                "Please try again or contact support if the issue persists.",
                chat_id
            )