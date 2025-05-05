# Standard library imports
from logging import getLogger

# Third-party imports
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

# Local application imports
from app.agent.configuration import AgentConfiguration
from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.utils import (
	create_error_response,
	fix_tool_call_sequence,
	format_llm_response,
)
from app.service.ticketing.client import BaseTicketingClient

from .rag.graph import create_rag_graph
from .state import AgentState
from .ticket_agent.graph import create_ticket_agent
from .tools import rag_tool, ticket_tool, tools_condition

logger = getLogger(__name__)


def create_agent_graph(
	checkpointer: AsyncPostgresSaver | None = None,
	ticketing_client: BaseTicketingClient | None = None,
) -> CompiledStateGraph:
	"""Create a new agent graph instance."""
	if ticketing_client is None:
		raise ValueError('Ticketing client is required for agent graph')

	ticket_graph = create_ticket_agent(checkpointer, ticketing_client)
	rag_graph = create_rag_graph(checkpointer, ticketing_client)

	builder = StateGraph(AgentState)

	tool_node = ToolNode([ticket_tool, rag_tool])

	builder.add_node('agent', call_model)
	builder.add_node('tools', tool_node)
	builder.add_node('ticket_agent', ticket_graph)
	builder.add_node('rag_agent', rag_graph)

	builder.set_entry_point('agent')
	builder.add_conditional_edges(
		'agent',
		tools_condition,
		{
			'tools': 'tools',
			'ticket_agent': 'ticket_agent',
			'rag_agent': 'rag_agent',
			'__end__': '__end__',
		},
	)
	builder.add_edge('tools', 'agent')
	builder.add_edge('ticket_agent', 'agent')
	builder.add_edge('rag_agent', 'agent')

	graph = builder.compile(checkpointer=checkpointer)
	return graph


async def call_model(state: AgentState, config: RunnableConfig):
	"""Node that calls the LLM with the current state."""
	conversation_messages = list(state.messages)
	agent_config = AgentConfiguration()

	checkpointer = config['configurable']['__pregel_checkpointer']
	llm = agent_config.get_llm(checkpointer=checkpointer)

	# Fix message sequence if user breaks the tool call interrupt approval step by sending a new message instead of approving the tool call
	sequence_info = fix_tool_call_sequence(conversation_messages)
	prepared_messages = sequence_info['prepared_messages']
	state_corrections = sequence_info['state_corrections']

	# Add system prompt to the beginning of the messages
	system_message = SystemMessage(content=AGENT_SYSTEM_PROMPT)
	messages_with_system = [system_message] + prepared_messages

	# Bind tools to the LLM
	llm_with_tools = llm.bind_tools([ticket_tool, rag_tool])

	try:
		model_response = await llm_with_tools.ainvoke(messages_with_system)
		return await format_llm_response(model_response, state_corrections, config)
	except Exception as e:
		return create_error_response(e, state_corrections)
