import logging
import uuid
from typing import Optional

from config import OPENAI_MODEL
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .chat_memory import ChatMemory
from .nodes import call_model, should_continue
from .rag.agent import create_retrieve_tool
from .ticketing_agent.ticketing_tool import create_ticketing_tool
from models import Project
from models.apikey import APIKey
from repositories.chat_session_repository import ChatSessionRepository

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, project: Project, api_key: APIKey, chat_session_repository: ChatSessionRepository):
        self.project = project
        self.api_key = api_key
        self.chat_session_repository = chat_session_repository
        self.memory = ChatMemory(chat_session_repository)
        
        # Create tools
        self.tools = [
            create_retrieve_tool(project, api_key),
            create_ticketing_tool(project, api_key)
        ]
        
        # Initialize LLM with tools
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0).bind_tools(self.tools, tool_choice="auto")
        
        # Initialize the workflow graph
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
    
    def _create_workflow(self) -> StateGraph:
        """Create the agent workflow graph."""
        workflow = StateGraph(MessagesState)
        
        # Create tool node
        tool_node = ToolNode(self.tools)
        
        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        
        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent", 
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow

    async def process_question(self, question: str, chat_id: Optional[str] = None) -> tuple[str, str]:
        """Process a user question through the agent workflow."""
        try:
            # Generate chat ID if not provided
            chat_id = chat_id or f"chat_{uuid.uuid4()}"
            logger.info(f"Processing question in chat {chat_id}: {question}")
            
            # Get history and add new question
            messages = await self.memory.get_chat_history(chat_id)
            messages.append(HumanMessage(content=question))
            
            # Create config for the run
            config = RunnableConfig(
                configurable={
                    "llm": self.llm,
                    "chat_id": chat_id
                }
            )
            
            # Process through workflow
            result = await self.app.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Get response and save to history
            answer = result["messages"][-1].content
            context = next((msg.content for msg in reversed(result["messages"]) 
                          if isinstance(msg, ToolMessage)), None)
                        
            await self.memory.add_to_chat_history(chat_id, question, answer, context)
            return answer, chat_id
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return ("I apologize, but I encountered an error. Please try again.", chat_id)
