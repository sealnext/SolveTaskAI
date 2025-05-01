import re
from functools import partial
from logging import getLogger
from typing import Annotated, List, Sequence

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph, add_messages
from pydantic import BaseModel, Field

from app.agent.configuration import AgentConfiguration
from app.dto.project import Project
from app.misc.postgres import connection_string_psycopg
from app.misc.settings import settings
from app.service.ticketing.client import BaseTicketingClient

logger = getLogger(__name__)


embeddings_model = OpenAIEmbeddings(model=settings.openai_embedding_model)

agent_config = AgentConfiguration()

llm = agent_config.get_llm()
llm_json_mode = agent_config.get_json_llm()

number_of_docs_to_retrieve = 5


class RAGState(BaseModel):
	"""State for the RAG (Retrieval-Augmented Generation) agent workflow.

	Contains all the state information needed throughout the RAG pipeline,
	including the question, retrieved documents, and intermediate results.
	"""

	messages: Annotated[Sequence[AnyMessage], add_messages] = []
	question: str | None = Field(None, description="The user's question/query to answer")
	documents: List[Document] = Field(default_factory=list, description='List of documents')
	project: Project | None = Field(None, description='The current project context')
	retry_retrieve_count: int = Field(0, description='Number of document retrieval attempts')
	ignore_tickets: List[str] = Field(
		default_factory=list, description='List of ticket IDs to ignore in retrieval'
	)

	class Config:
		arbitrary_types_allowed = True


async def create_vector_store(unique_identifier_project: str):
	"""Create a PGVector store for the given project."""
	return PGVector(
		embeddings=embeddings_model,
		collection_name=unique_identifier_project,
		connection=connection_string_psycopg,
		pre_delete_collection=False,
		async_mode=True,
	)


async def retrieve_documents(state: RAGState, client: BaseTicketingClient) -> RAGState:
	"""Retrieve relevant documents for the given question."""
	try:
		# Extract question from last message
		query = state.messages[1].tool_calls[0]['args']['query']

		state.question = query
		state.project = client.project

		project_id = f'{re.sub(r"^https?://|/$", "", state.project.domain)}/{state.project.key}/{state.project.external_id}'
		vector_store = await create_vector_store(project_id)

		k = number_of_docs_to_retrieve * (state.retry_retrieve_count + 1)
		documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
			await embeddings_model.aembed_query(state.question),
			k=k,
		)

		docs = [doc.metadata['key'] for doc, _ in documents_with_scores]
		documents = await fetch_documents(docs, client)

		state.messages = str(documents)
		state.retry_retrieve_count += 1
		return state

	except Exception as e:
		state.messages = str(e)
		return state


async def fetch_documents(
	docs: list[str],
	client: BaseTicketingClient,
) -> list[Document]:
	"""Fetch full content for documents from the ticketing system."""
	if not docs:
		return []

	documents = []

	for ticket_id in docs:
		ticket = await client.get_ticket(ticket_id)
		documents.append(str(ticket))

	return documents


def create_rag_graph(
	checkpointer: AsyncPostgresSaver | None = None,
	client: BaseTicketingClient | None = None,
):
	"""Create and configure a RAG (Retrieval-Augmented Generation) agent graph.

	Args:
	    checkpointer: Optional async postgres checkpoint saver
	    client: Ticketing client for document retrieval (required)

	Returns:
	    Configured StateGraph ready for execution

	Raises:
	    ValueError: If required client is not provided
	"""
	if client is None:
		raise ValueError('Ticketing client is required for RAG graph')

	logger.info('Initializing RAG agent graph')

	# Initialize graph with RAGState
	builder = StateGraph(RAGState)

	# Add all workflow nodes
	builder.add_node('retrieve', partial(retrieve_documents, client=client))
	builder.add_node('agent', lambda state: state)

	# Configure workflow edges
	builder.set_entry_point('retrieve')
	builder.add_edge('retrieve', END)

	# Compile and return the graph
	graph = builder.compile(checkpointer=checkpointer)
	logger.info('RAG agent graph successfully compiled')
	return graph
