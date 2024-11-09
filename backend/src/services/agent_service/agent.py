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
from .tools.ticketing_tool import TicketingTool
from .prompts import main_prompt_template, ticketing_actions_template
from langgraph.prebuilt import ToolNode

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, project: Project, api_key: APIKey, chat_session_repository: ChatSessionRepository):
        self.project = project
        self.api_key = api_key
        self.chat_session_repository = chat_session_repository
        self.memory = ChatMemory(chat_session_repository)
        
        # Initialize tools with clearer descriptions
        self.retrieve_tool = RetrieveDocuments(project=project, api_key=api_key)
        self.ticketing_tool = TicketingTool(project=project, api_key=api_key)
        
        # Initialize LLM with tools and clear descriptions
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        
        # Override tool descriptions to be more specific
        retrieve_tool = self.retrieve_tool.to_tool()
        retrieve_tool.description = """
        Use this tool for searching and retrieving information from tickets and documentation.
        ALWAYS use this tool for:
        - Finding information about bugs, issues, or features
        - Searching through ticket content
        - Getting context about specific topics
        - Answering questions about existing tickets
        - Finding how many tickets match certain criteria
        
        Do NOT use this tool for:
        - Creating new tickets
        - Updating existing tickets
        - Any actions that modify tickets
        - Questions about ability to modify tickets
        """
        
        self.ticketing_tool.description = """
        Use this tool for ALL ticket-related operations and questions, including:
        - Creating, updating, or modifying tickets
        - Questions about ability to modify tickets (e.g., "can you edit...", "are you able to change...")
        - Checking permissions for ticket operations
        - Any request that involves ticket modifications
        - Any question about ticket modification capabilities
        
        ALWAYS forward these types of requests to this tool:
        - "Can you edit..."
        - "Are you able to modify..."
        - "Is it possible to change..."
        - Any question about ticket modifications
        
        Let the ticketing tool handle the response and necessary clarifications.
        Do NOT answer these questions directly - forward them to the tool.
        """
        
        self.llm_with_tools = self.llm.bind_tools(
            [retrieve_tool, self.ticketing_tool],
            tool_choice="auto"
        )
        
        # Initialize the workflow graph
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # Add system message with ticketing context
        self.system_message = SystemMessage(content=ticketing_actions_template.format(
            service_type=project.service_type.value,
            project_key=project.key
        ))

    def _create_workflow(self) -> StateGraph:
        """Create the agent workflow."""
        workflow = StateGraph(MessagesState)
        
        # Create a configured call_model node with the LLM
        async def configured_call_model(state):
            state["config"] = {"llm": self.llm_with_tools}
            result = await call_model(state)
            
            # Just log the tool being used, without interpreting the request
            if "tool_calls" in result.get("messages", [])[-1].additional_kwargs:
                tool_calls = result["messages"][-1].additional_kwargs["tool_calls"]
                for tool_call in tool_calls:
                    logger.info(f"Forwarding request to tool: {tool_call['function']['name']}")
            
            return result
        
        # Add nodes
        workflow.add_node("agent", configured_call_model)
        
        # Create a tool node that passes conversation history
        async def tool_node_with_history(state):
            messages = state["messages"]
            history = [{
                "role": msg.type,
                "content": msg.content
            } for msg in messages[:-1]]
            
            # Create new TicketingTool instance with history
            ticketing_tool_with_history = TicketingTool(
                project=self.project,
                api_key=self.api_key,
                conversation_history=history
            )
            
            tools = [
                self.retrieve_tool.to_tool(),
                ticketing_tool_with_history
            ]
            
            return await ToolNode(tools).ainvoke(state)
        
        workflow.add_node("tools", tool_node_with_history)
        
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
        """Process a question using the agent workflow."""
        logger.info(f"Processing question: {question}")
        
        if not chat_id:
            chat_id = f"chat_{uuid.uuid4()}"
            logger.info(f"Created new chat session: {chat_id}")
        
        try:
            # Get chat history
            messages = await self.memory.get_chat_history(chat_id)
            
            # Always include the system message first
            if not messages or messages[0].type != "system":
                messages = [self.system_message] + messages
            
            # Add the new question
            messages.append(HumanMessage(content=question))
            
            # Run the workflow
            result = await self.app.ainvoke({
                "messages": messages,
                "config": {"llm": self.llm_with_tools}
            })
            
            # Extract the final answer and context
            answer, context = extract_final_response(result)
            
            # Save to chat history including any ticket IDs found
            await self.memory.add_to_chat_history(chat_id, question, answer, context)
            
            return answer, chat_id
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return (
                "I apologize, but I encountered an error while processing your question. "
                "Please try again or contact support if the issue persists.",
                chat_id
            )