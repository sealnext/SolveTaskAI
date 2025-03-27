import re
from functools import partial
from typing import List, Optional
from langgraph.graph import StateGraph, END
import logging
from app.schemas.project import Project
from pydantic import BaseModel, Field
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.schemas.project import Project
from langchain_core.documents import Document
from app.services.ticketing.client import BaseTicketingClient
from app.config.config import (
    OPENAI_EMBEDDING_MODEL,
    DATABASE_URL,
    NUMBER_OF_DOCS_TO_RETRIEVE,
)
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import json
from langchain.schema import SystemMessage, HumanMessage
from app.agent.configuration import AgentConfiguration
from app.agent.rag.prompts import doc_grader_instructions, doc_grader_prompt
import asyncio

class RAGState(BaseModel):
    """State for the RAG (Retrieval-Augmented Generation) agent workflow.
    
    Contains all the state information needed throughout the RAG pipeline,
    including the question, retrieved documents, and intermediate results.
    """
    question: str = Field(..., description="The user's question/query to answer")
    documents: List[Document] = Field(default_factory=list,
                                    description="List of retrieved documents")
    project: Project = Field(..., description="The current project context")
    retry_retrieve_count: int = Field(0,
                                    description="Number of document retrieval attempts")
    ignore_tickets: List[str] = Field(default_factory=list,
                                    description="List of ticket IDs to ignore in retrieval")
    
    class Config:
        arbitrary_types_allowed = True

logger = logging.getLogger(__name__)


embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

agent_config = AgentConfiguration()
llm = agent_config.get_llm()

llm_json_mode = llm.bind(response_format={"type": "json_object"})

# Create a SQLAlchemy engine
engine = create_async_engine(DATABASE_URL)

# Create a session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_vector_store(unique_identifier_project: str):
    """Create a PGVector store for the given project."""
    return PGVector(
        embeddings=embeddings_model,
        collection_name=unique_identifier_project,
        connection=DATABASE_URL,
        pre_delete_collection=False,
        async_mode=True,
    )


async def retrieve_documents(state: RAGState, client: BaseTicketingClient) -> RAGState:
    """Retrieve relevant documents for the given question.
    
    Args:
        state: Current RAG state containing question and context
        client: Ticketing client for fetching document content
        
    Returns:
        Updated RAG state with retrieved documents
        
    Raises:
        ValueError: If required state fields are missing
    """
    logger.info("--- Starting document retrieval ---")
    
    try:
        # Validate required state fields
        if not state.question or not state.project:
            raise ValueError("State must contain question and project")
            
        logger.info(
            f"Retrieving documents for question: {state.question[:50]}..., "
            f"Retry attempt: {state.retry_retrieve_count}"
        )

        # Generate query embedding
        query_embedding = await embeddings_model.aembed_query(state.question)
        
        # Create project-specific vector store
        project_id = (
            f"{re.sub(r'^https?://|/$', '', state.project.domain)}/"
            f"{state.project.key}/{state.project.internal_id}"
        )
        vector_store = await create_vector_store(project_id)

        # Calculate number of documents to retrieve
        k = NUMBER_OF_DOCS_TO_RETRIEVE * (state.retry_retrieve_count + 1)
        
        # Retrieve documents with similarity scores
        documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
            query_embedding,
            k=k,
        )

        # Filter out ignored tickets
        filtered_docs = [
            (doc, score)
            for doc, score in documents_with_scores
            if doc.metadata["key"] not in state.ignore_tickets
        ][:NUMBER_OF_DOCS_TO_RETRIEVE]

        # Fetch full document content
        documents = await fetch_documents(state, filtered_docs, client)

        logger.info(f"Successfully retrieved {len(documents)} documents")
        
        # Update and return state
        state.documents = documents
        state.retry_retrieve_count += 1
        return state
        
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        raise


async def retry_retrieve_documents(state: RAGState, client: BaseTicketingClient) -> RAGState:
    """Retry document retrieval with expanded parameters when initial retrieval fails.
    
    Args:
        state: Current RAG state containing question and context
        client: Ticketing client for fetching document content
        
    Returns:
        Updated RAG state with retrieved documents
        
    Raises:
        ValueError: If required state fields are missing
    """
    logger.info("--- Starting retry document retrieval ---")
    
    try:
        # Validate required state fields
        if not state.question or not state.project:
            raise ValueError("State must contain question and project")
            
        logger.info(
            f"Retrying document retrieval for question: {state.question[:50]}..., "
            f"Previous attempts: {state.retry_retrieve_count}"
        )

        # Generate query embedding
        query_embedding = await embeddings_model.aembed_query(state.question)
        
        # Create project-specific vector store
        project_id = (
            f"{re.sub(r'^https?://|/$', '', state.project.domain)}/"
            f"{state.project.key}/{state.project.internal_id}"
        )
        vector_store = await create_vector_store(project_id)

        # Retrieve more documents on retry
        k = NUMBER_OF_DOCS_TO_RETRIEVE * 2
        
        # Retrieve documents with similarity scores
        documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
            query_embedding,
            k=k,
        )

        # Filter out ignored tickets
        filtered_docs = [
            (doc, score)
            for doc, score in documents_with_scores
            if doc.metadata["key"] not in state.ignore_tickets
        ][:NUMBER_OF_DOCS_TO_RETRIEVE]

        # Fetch full document content
        documents = await fetch_documents(state, filtered_docs, client)

        logger.info(f"Retrieved {len(documents)} documents on retry")
        
        # Update and return state
        state.documents = documents
        state.retry_retrieve_count += 1
        return state
        
    except Exception as e:
        logger.error(f"Document retrieval retry failed: {str(e)}")
        raise


async def grade_documents(
    state: RAGState,
    client: BaseTicketingClient,
    min_relevance_score: float = 0.7,
    max_ignore_tickets: int = 100
) -> RAGState:
    """Grade retrieved documents for relevance to the question.
    
    Args:
        state: Current RAG state containing documents to grade
        client: Ticketing client (unused in grading but kept for consistency)
        min_relevance_score: Minimum score to consider document relevant (0-1)
        max_ignore_tickets: Maximum number of tickets to ignore
        
    Returns:
        Updated RAG state with filtered documents and updated ignore list
        
    Raises:
        ValueError: If required state fields are missing or invalid
    """
    logger.info("--- Starting document grading ---")
    
    try:
        # Validate inputs
        if not state.question or not state.documents:
            raise ValueError("State must contain question and documents")
        if not 0 <= min_relevance_score <= 1:
            raise ValueError("min_relevance_score must be between 0 and 1")

        logger.info(f"Grading {len(state.documents)} documents for relevance")

        async def grade_single_document(doc: Document) -> tuple[Document, float]:
            """Grade a single document and return relevance score (0-1)."""
            logger.debug(f"Grading document: {doc.metadata['key']}")

            try:
                # Format and send grading prompt to LLM
                prompt = doc_grader_prompt.format(
                    document=doc,
                    question=state.question
                )
                
                result = await llm_json_mode.ainvoke([
                    SystemMessage(content=doc_grader_instructions),
                    HumanMessage(content=prompt)
                ])
                
                # Validate and parse LLM response
                try:
                    response = json.loads(result.content)
                    if "binary_score" not in response or "confidence" not in response:
                        raise ValueError("Invalid LLM response format")
                    score = 1.0 if response["binary_score"].lower() == "yes" else 0.0
                    confidence = float(response["confidence"])
                    return doc, score * confidence
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Invalid grade response for {doc.metadata['key']}: {str(e)}")
                    return doc, 0.0
                
            except Exception as e:
                logger.error(f"Failed to grade document {doc.metadata['key']}: {str(e)}")
                return doc, 0.0

        # Grade all documents in parallel with timeout
        try:
            grading_results = await asyncio.wait_for(
                asyncio.gather(*[grade_single_document(doc) for doc in state.documents]),
                timeout=len(state.documents) * 5  # 5 seconds per doc
            )
        except asyncio.TimeoutError:
            logger.error("Document grading timed out")
            raise ValueError("Grading operation timed out")

        # Filter documents based on scores
        filtered_docs = []
        new_ignored = []
        
        for doc, score in grading_results:
            if score >= min_relevance_score:
                logger.debug(f"Document {doc.metadata['key']} scored {score:.2f} (relevant)")
                filtered_docs.append(doc)
            else:
                logger.debug(f"Document {doc.metadata['key']} scored {score:.2f} (ignored)")
                new_ignored.append(doc.metadata["key"])

        # Update state with size-limited ignore list
        state.documents = filtered_docs
        updated_ignore = list(set(state.ignore_tickets + new_ignored))[:max_ignore_tickets]
        state.ignore_tickets = updated_ignore
        
        logger.info(f"Kept {len(filtered_docs)}/{len(state.documents)} relevant documents")
        return state
        
    except Exception as e:
        logger.error(f"Document grading failed: {str(e)}")
        raise


async def fetch_documents(
    state: RAGState,
    documents_with_scores: list[tuple[Document, float]],
    client: BaseTicketingClient,
    max_retries: int = 2,
    timeout: float = 10.0
) -> list[Document]:
    """Fetch full content for documents from the ticketing system.
    
    Args:
        state: Current RAG state (unused but kept for consistency)
        documents_with_scores: List of (document, score) tuples
        client: Ticketing client for fetching document content
        max_retries: Maximum number of retry attempts per document
        timeout: Timeout in seconds for each fetch attempt
        
    Returns:
        List of documents with populated content
        
    Raises:
        ValueError: If input documents are invalid
    """
    if not documents_with_scores:
        logger.warning("No documents to fetch")
        return []

    documents = []
    fetch_errors = 0
    
    async def fetch_with_retry(ticket_id: str) -> Optional[str]:
        """Helper function to fetch ticket content with retries"""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with asyncio.timeout(timeout):
                    ticket = await client.get_ticket(ticket_id)
                    if not ticket.content or not isinstance(ticket.content, str):
                        raise ValueError("Invalid ticket content")
                    return ticket.content
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed for ticket {ticket_id}: {str(e)}")
        logger.error(f"Failed to fetch ticket {ticket_id} after {max_retries} retries")
        return None

    for doc, score in documents_with_scores:
        if not doc.metadata or "key" not in doc.metadata:
            logger.error("Document missing required metadata")
            continue

        ticket_id = doc.metadata["key"]
        try:
            logger.debug(f"Fetching ticket {ticket_id}")
            content = await fetch_with_retry(ticket_id)
            if content is None:
                fetch_errors += 1
                continue
                
            doc.page_content = content
            documents.append(doc)
            
        except Exception as e:
            fetch_errors += 1
            logger.error(f"Unexpected error processing ticket {ticket_id}: {str(e)}")
            continue

    if fetch_errors:
        logger.warning(f"Failed to fetch {fetch_errors} documents")

    return documents

def decide_after_grading(state: RAGState) -> str:
    """Determine next step after document grading.
    
    Args:
        state: Current RAG state after document grading
        
    Returns:
        "generate" if ready to generate answer
        "retry" if should retry document retrieval
    """
    logger.debug(
        f"Deciding next step - Retries: {state.retry_retrieve_count}, "
        f"Documents: {len(state.documents)}"
    )
    
    if state.retry_retrieve_count >= 2 or len(state.documents) > 0:
        logger.info("Proceeding to answer generation")
        return "generate"
        
    logger.info("Retrying document retrieval")
    return "retry"

def create_rag_graph(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    client: Optional[BaseTicketingClient] = None,
) -> StateGraph:
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
        raise ValueError("Ticketing client is required for RAG graph")
        
    logger.info("Initializing RAG agent graph")

    # Initialize graph with RAGState
    builder = StateGraph(RAGState)

    # Add all workflow nodes
    builder.add_node("retrieve", partial(retrieve_documents, client=client))
    builder.add_node("retry_retrieval", partial(retry_retrieve_documents, client=client))
    builder.add_node("grade_documents", partial(grade_documents, client=client))
    builder.add_node("agent", lambda state: state)  # Placeholder for answer generation

    # Configure workflow edges
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "grade_documents")
    builder.add_edge("retry_retrieval", "grade_documents")
    
    # Add conditional routing after grading
    builder.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "retry": "retry_retrieval",
            "generate": "agent"
        },
    )
    
    builder.add_edge("agent", END)
    
    # Compile and return the graph
    graph = builder.compile(checkpointer=checkpointer)
    logger.info("RAG agent graph successfully compiled")
    return graph
