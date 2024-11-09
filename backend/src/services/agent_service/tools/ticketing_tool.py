from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from models import Project, APIKey
from config.enums import TicketingSystemType
import logging
from ..jira_client import JiraClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ..prompts import ticketing_actions_template
import json
from config import OPENAI_MODEL
logger = logging.getLogger(__name__)

class TicketingInput(BaseModel):
    """Input for the ticketing tool."""
    request: str = Field(..., description="The ticketing action request to process")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages with their roles and content"
    )

class TicketingTool(BaseTool):
    name: str = "manage_tickets"
    description: str = """
    Manages tickets in the ticketing system. Forward any ticketing-related requests here, such as:
    - Viewing ticket information
    - Creating new tickets
    - Updating existing tickets
    - Linking tickets
    - Searching for tickets
    
    Simply forward the user's request as-is, don't try to interpret or modify it.
    """
    args_schema: type[BaseModel] = TicketingInput
    
    def __init__(self, project: Project, api_key: APIKey, conversation_history: List[Dict[str, str]] = None):
        super().__init__()
        self._project = project
        self._api_key = api_key
        self._conversation_history = conversation_history or []
        self._client = self._initialize_client()
        
        # Initialize sub-tools
        self._tools = {
            "create_task": CreateTaskTool(self._client),
            "update_task": UpdateTaskTool(self._client),
            "link_tickets": LinkTicketsTool(self._client),
            "get_ticket": GetTicketTool(self._client),
            "search_tickets": SearchTicketsTool(self._client)
        }
        
        # Initialize LLM for the ticketing agent
        self._llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        self._llm_with_tools = self._llm.bind_tools(
            list(self._tools.values()),
            tool_choice="auto"
        )

    def _run(self, request: str) -> str:
        """Synchronous version - not supported."""
        raise NotImplementedError("TicketingTool only supports async operations")

    async def _arun(self, request: str) -> str:
        """Process a ticketing request using the specialized ticketing agent."""
        try:
            # Start with system message
            messages = [
                SystemMessage(content=ticketing_actions_template.format(
                    service_type=self._project.service_type.value,
                    project_key=self._project.key
                ))
            ]
            
            # Add conversation history
            for msg in self._conversation_history:
                if msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add the current request exactly as received
            messages.append(HumanMessage(content=request))
            
            # Log the input messages
            logger.info("TicketingTool: Processing request with context:")
            logger.info(json.dumps([{
                "role": msg.type,
                "content": msg.content
            } for msg in messages[-2:]], indent=2))
            
            # Let the specialized LLM decide what to do
            response = await self._llm_with_tools.ainvoke(messages)
            
            # Log the response
            logger.info("TicketingTool: LLM Response:")
            logger.info(json.dumps({
                "content": response.content,
                "additional_kwargs": response.additional_kwargs,
                "type": response.type,
            }, indent=2))
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error processing ticketing request: {e}", exc_info=True)
            return f"Failed to process ticketing request: {str(e)}"

    def _initialize_client(self):
        if self._project.service_type == TicketingSystemType.JIRA:
            return JiraClient(
                domain=self._api_key.domain,
                api_key=self._api_key.api_key,
                project_key=self._project.key
            )
        elif self._project.service_type == TicketingSystemType.AZURE:
            return AzureClient(
                domain=self._api_key.domain,
                api_key=self._api_key.api_key,
                project_key=self._project.key
            )
        else:
            raise ValueError(f"Unsupported service type: {self._project.service_type}")

# Specialized sub-tools
class CreateTaskTool(BaseTool):
    name: str = "create_task"
    description: str = "Creates a new task, story, or sub-task in the ticketing system"
    client: Any = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client):
        logger.info(f"CreateTaskTool: Initializing CreateTaskTool with client: {client}")
        super().__init__(client=client)
        self._client = client
    
    def _run(self, title: str, description: str, 
             acceptance_criteria: List[str], estimate: str,
             parent_ticket: Optional[str] = None) -> str:
        raise NotImplementedError("CreateTaskTool only supports async operations")

    async def _arun(self, title: str, description: str, 
                    acceptance_criteria: List[str], estimate: str,
                    parent_ticket: Optional[str] = None) -> str:
        logger.info(f"CreateTaskTool: Creating task with title: {title}, description: {description}, acceptance criteria: {acceptance_criteria}, estimate: {estimate}, parent ticket: {parent_ticket}")
        task = await self._client.create_task({
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "estimate": estimate,
            "parent_ticket": parent_ticket
        })
        return f"Created task {task['key']}: {task['url']}"

class UpdateTaskTool(BaseTool):
    name: str = "update_task"
    description: str = "Updates an existing ticket with new information"
    client: Any = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client):
        logger.info(f"UpdateTaskTool: Initializing UpdateTaskTool with client: {client}")
        super().__init__(client=client)
        self._client = client
    
    def _run(self, ticket_id: str, updates: Dict[str, Any]) -> str:
        raise NotImplementedError("UpdateTaskTool only supports async operations")

    async def _arun(self, ticket_id: str, updates: Dict[str, Any]) -> str:
        logger.info(f"UpdateTaskTool: Updating ticket {ticket_id} with updates: {updates}")
        result = await self._client.update_task(ticket_id, updates)
        return f"Updated ticket {result['key']}"

class LinkTicketsTool(BaseTool):
    name: str = "link_tickets"
    description: str = "Creates links between related tickets"
    client: Any = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client):
        logger.info(f"LinkTicketsTool: Initializing LinkTicketsTool with client: {client}")
        super().__init__(client=client)
        self._client = client
    
    def _run(self, source_ticket: str, target_ticket: str, link_type: str) -> str:
        raise NotImplementedError("LinkTicketsTool only supports async operations")

    async def _arun(self, source_ticket: str, target_ticket: str, link_type: str) -> str:
        logger.info(f"LinkTicketsTool: Creating {link_type} link between {source_ticket} and {target_ticket}")
        await self._client.link_tickets(source_ticket, target_ticket, link_type)
        return f"Created {link_type} link between {source_ticket} and {target_ticket}"

class GetTicketTool(BaseTool):
    name: str = "get_ticket"
    description: str = "Retrieves detailed information about a specific ticket"
    client: Any = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client):
        logger.info(f"GetTicketTool: Initializing GetTicketTool with client: {client}")
        super().__init__(client=client)
        self._client = client
    
    def _run(self, ticket_id: str) -> str:
        raise NotImplementedError("GetTicketTool only supports async operations")

    async def _arun(self, ticket_id: str) -> str:
        logger.info(f"GetTicketTool: Getting ticket with ID: {ticket_id}")
        ticket = await self._client.get_ticket(ticket_id)
        return str(ticket)

class SearchTicketsTool(BaseTool):
    name: str = "search_tickets"
    description: str = "Searches for tickets matching specific criteria"
    client: Any = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, client):
        logger.info(f"SearchTicketsTool: Initializing SearchTicketsTool with client: {client}")
        super().__init__(client=client)
        self._client = client
    
    def _run(self, query: str) -> str:
        raise NotImplementedError("SearchTicketsTool only supports async operations")

    async def _arun(self, query: str) -> str:
        logger.info(f"SearchTicketsTool: Searching for tickets with query: {query}")
        tickets = await self._client.search_tickets(query)
        return str(tickets)