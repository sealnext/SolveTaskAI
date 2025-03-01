from app.config.config import (
    OPENAI_EMBEDDING_MODEL,
    DATABASE_URL,
    NUMBER_OF_DOCS_TO_RETRIEVE,
    OPENAI_MODEL,
)
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from app.agent.state import AgentState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import re
import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging

from app.agent.rag.prompts import doc_grader_instructions, doc_grader_prompt
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
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


async def retrieve_documents(state: Dict[str, Any]) -> AgentState:
    logger.info("--- Retrieving documents node ---")
    question = state["question"]
    retry_retrieve_count = state.get("retry_retrieve_count", 0)
    ignore_tickets = state.get("ignore_tickets", [])

    logger.info(f"Question: {question}, Retry count: {retry_retrieve_count}")

    query_embedding = await embeddings_model.aembed_query(question)

    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', state['project'].domain)}/{state['project'].key}/{state['project'].internal_id}"
    vector_store = create_vector_store(unique_identifier_project)

    k = NUMBER_OF_DOCS_TO_RETRIEVE * (retry_retrieve_count + 1)
    documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
        query_embedding,
        k=k,
    )

    # Filter out ignored tickets
    documents_with_scores = [
        (doc, score)
        for doc, score in documents_with_scores
        if doc.metadata["key"] not in ignore_tickets
    ][:NUMBER_OF_DOCS_TO_RETRIEVE]

    documents = await fetch_documents(state, documents_with_scores)

    logger.info(f"Retrieved {len(documents)} documents")

    state["documents"] = documents
    state["retry_retrieve_count"] = retry_retrieve_count + 1
    return state


async def retry_retrieve_documents(state):
    logger.info("--- Retry Retrieve Documents Node ---")
    question = state["question"]
    ignore_tickets = state.get("ignore_tickets", [])

    query_embedding = await embeddings_model.aembed_query(question)

    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', state['project'].domain)}/{state['project'].key}/{state['project'].internal_id}"
    vector_store = create_vector_store(unique_identifier_project)

    k = NUMBER_OF_DOCS_TO_RETRIEVE * 2  # Try with double the documents on retry
    documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
        query_embedding,
        k=k,
    )

    # Filter out ignored tickets
    documents_with_scores = [
        (doc, score)
        for doc, score in documents_with_scores
        if doc.metadata["key"] not in ignore_tickets
    ][:NUMBER_OF_DOCS_TO_RETRIEVE]

    documents = await fetch_documents(state, documents_with_scores)

    logger.info(f"Retrieved {len(documents)} documents on retry")
    state["documents"] = documents
    state["retry_retrieve_count"] = state.get("retry_retrieve_count", 0) + 1

    return state


async def grade_documents(state: AgentState) -> dict:
    logger.info("--- Grading documents node ---")

    question = state["question"]
    documents = state["documents"]

    ignore_tickets = state.get("ignore_tickets", [])

    async def grade_single_document(doc):
        logger.info(f"Grading document: {doc.metadata['key']}")

        doc_grader_prompt_formatted = doc_grader_prompt.format(
            document=doc, question=question
        )

        result = await llm_json_mode.ainvoke(
            [SystemMessage(content=doc_grader_instructions)]
            + [HumanMessage(content=doc_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]

        return doc, grade.lower() == "yes"

    # Run grading for all documents in parallel
    grading_results = await asyncio.gather(
        *[grade_single_document(doc) for doc in documents]
    )

    filtered_docs = []
    for doc, is_relevant in grading_results:
        if is_relevant:
            logger.debug(f"Document {doc.metadata['key']} graded as relevant")
            filtered_docs.append(doc)
        else:
            logger.debug(f"Document {doc.metadata['key']} graded as not relevant")
            ignore_tickets.append(doc.metadata["key"])

    state["documents"] = filtered_docs
    state["ignore_tickets"] = list(set(ignore_tickets))  # Remove duplicates
    return state


async def fetch_documents(state, documents_with_scores):
    data_extractor = create_data_extractor(state["api_key"])

    ticket_urls = [doc.metadata["key"] for doc, _ in documents_with_scores]
    fetched_documents = await data_extractor.get_tickets_parallel(ticket_urls)

    documents = []
    for (doc, score), fetched_doc in zip(documents_with_scores, fetched_documents):
        doc.page_content = fetched_doc.content.model_dump()
        documents.append(doc)

    return documents


async def generate_embeddings(state: Dict[str, Any]) -> AgentState:
    """Generate embeddings for documents."""
    logger.debug("Node: generate_embeddings called")

    unique_identifier_project = state["project_id"]
    vector_store = await create_vector_store(unique_identifier_project)

    try:
        # Add documents to vector store
        await vector_store.aadd_documents(state["documents"])
        logger.info(
            f"Added {len(state['documents'])} documents to collection {unique_identifier_project}"
        )
    except Exception as e:
        logger.error(f"Error adding documents to vector store: {e}")
        raise

    return AgentState(
        project_id=state["project_id"],
        documents=state["documents"],
        embeddings_generated=True,
    )
