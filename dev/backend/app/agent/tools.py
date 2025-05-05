from typing import Any, Literal, Union

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from pydantic import BaseModel

# rag_tool & ticket_tool serves as a declarative interface for the ticket_tool subgraph.
# While it appears as a standard tool to the LLM, it actually orchestrates
# a more complex workflow by routing to the dedicated ticket_tool node.
# The actual implementation is handled by the ticket_tool subgraph, with
# flow control managed by the tools_condition function which directs
# tool calls to the appropriate node.

# We use this approach because LangGraph automatically handles checkpointer propagation
# to child sub-graphs, eliminating the need for manual implementation. However, LangGraph
# has limitations when sub-graphs are manually invoked from tools, which is why we need
# this specific architecture.


@tool
async def rag_tool(query: str) -> str:
	"""
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

	Args:
	    query: The search query to use for document retrieval

	Returns:
	    String containing the retrieved documents or empty if none found
	"""
	return {}


async def ticket_tool(
	action: Literal['create', 'edit', 'delete'], ticket_id: str, detailed_query: str
):
	"""Tool for handling complex ticket operations, like creating, editing, or deleting tickets.

	Parameters:
	- action: create, edit, delete, search
	- ticket_id (optional): the id of the ticket to be created, edited or deleted
	- detailed_query: the detailed query to be used for the ticket
	"""
	return {}


# This is a custom tool condition that determines the next node based on the current state
# This is used to route tool calls to the appropriate subgraph
# If a tool is invoked we handled it in the subgraph tool node
# we do this because LangGraph has limitations when subgraphs are manually invoked from tools
# we invoke the subgraph tool node to handle the checkpointer propagation
def tools_condition(
	state: Union[list[AnyMessage], dict[str, Any], BaseModel],
) -> Literal['tools', 'ticket_agent', 'rag_agent', '__end__']:
	if isinstance(state, list):
		ai_message = state[-1]
	elif isinstance(state, dict) and (messages := state.get('messages', [])):
		ai_message = messages[-1]
	elif messages := getattr(state, 'messages', []):
		ai_message = messages[-1]
	else:
		raise ValueError(f'No messages found in input state to tool_edge: {state}')

	# Check if AI message is a tool call invocation
	if hasattr(ai_message, 'tool_calls') and len(ai_message.tool_calls) > 0:
		tool_name = ai_message.tool_calls[0]['name']
		if tool_name == 'ticket_tool':
			return 'ticket_agent'
		elif tool_name == 'rag_tool':
			return 'rag_agent'
		return 'tools'
	return '__end__'
