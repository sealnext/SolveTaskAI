import logging
import re
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.schema import Document

from config import OPENAI_EMBEDDING_MODEL, DATABASE_URL
from services.data_extractor.data_extractor_factory import create_data_extractor
from .state import AgentState

logger = logging.getLogger(__name__)

embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

# Create a SQLAlchemy engine
engine = create_async_engine(DATABASE_URL)

# Create a session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def create_vector_store(unique_identifier_project: str):
    return PGVector(
        embeddings=embeddings_model,
        collection_name=unique_identifier_project,
        connection=DATABASE_URL,
        pre_delete_collection=False,
        async_mode=True
    )
    
# Delete Embeddings
async def delete_embeddings(state: AgentState) -> AgentState:
    logger.debug("Node: delete_embeddings called")
    logger.debug(f"State: {state}")
    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', state['project'].domain)}/{state['project'].key}/{state['project'].internal_id}"
    logger.debug(f"Unique identifier project to delete: {unique_identifier_project}")
    vector_store = create_vector_store(unique_identifier_project)
    # TODO THIS adelete is not working
    await vector_store.adelete_collection()
    return {"status": "success"}

# Document Processing Nodes
async def access_documents_with_api_key(state: AgentState) -> AgentState:
    logger.debug("Node: access_documents_with_api_key called")
    project_id = state["project"].id
    project_key = state["project"].key
    api_key = state["api_key"]
    
    if not all([project_id, project_key, api_key]):
        raise HTTPException(status_code=400, detail="Missing required state data")
    
    logger.info(f"Accessing documents for project {project_id}")
    data_extractor = create_data_extractor(api_key)
    tickets = await data_extractor.get_all_tickets(project_key, project_id)
    
    logger.info(f"🎯 AccessDocumentsWithApiKey: Tickets: {tickets}")
    
    state["tickets"] = tickets
    return state

# Generate Embeddings
async def generate_embeddings(state: dict) -> dict:
    logger.debug("Node: generate_embeddings called")
    tickets = state["tickets"]
    project = state["project"]
    
    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', project.domain)}/{project.key}/{project.internal_id}"
    
    async with AsyncSessionLocal() as session:
        query = text("SELECT EXISTS (SELECT 1 FROM langchain_pg_collection WHERE name = :name)")
        result = await session.execute(query, {"name": unique_identifier_project})
        collection_exists = result.scalar()

        if collection_exists:
            logger.info(f"Collection {unique_identifier_project} already exists. Skipping embedding generation.")
            domain_with_slash = project.domain if project.domain.endswith('/') else f"{project.domain}/"
            return {"status": f"Collection for {domain_with_slash}browse/{project.key} already exists.", "tickets": []}
        
        logger.info(f"Creating new collection for {unique_identifier_project} and generating embeddings.")
        
        vector_store = create_vector_store(unique_identifier_project)
        
        batch_size = 100
        for i in range(0, len(tickets), batch_size):
            batch_tickets = tickets[i:i+batch_size]
            
            embedding_texts = [ticket.embedding_vector for ticket in batch_tickets]
            metadatas = [{
                'ticket_url': ticket.ticket_url,
                'issue_type': ticket.issue_type,
                'status': ticket.status,
                'priority': ticket.priority,
                'sprint': ticket.sprint,
                'key': ticket.ticket_api,
                'labels': ticket.labels,
                'resolution': ticket.resolution,
                'parent': ticket.parent,
                'assignee': ticket.assignee,
                'reporter': ticket.reporter,
                'resolutiondate': ticket.resolutiondate,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            } for ticket in batch_tickets]

            embeddings = await embeddings_model.aembed_documents(embedding_texts)
            
            logger.info(f"Generated {len(embeddings)} embeddings for batch {i//batch_size + 1}")
            
            # Log sample embeddings
            for idx in range(min(5, len(embeddings))):
                logger.info(f"Sample embedding {idx} length: {len(embeddings[idx])}")
                logger.info(f"Sample embedding {idx} preview: {embeddings[idx][:5]}...")
            
            await vector_store.aadd_embeddings(
                texts=[""] * len(embeddings),
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Processed and added batch {i//batch_size + 1} of {len(tickets)//batch_size + 1} to vector store")

        logger.info(f"Finished adding {len(tickets)} documents to the vector store.")
    
    return {"tickets": tickets, "status": "success"}
