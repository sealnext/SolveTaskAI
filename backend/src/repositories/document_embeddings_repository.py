import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import OPENAI_EMBEDDING_MODEL, DATABASE_URL
from models.document_embeddings import DocumentEmbedding

logger = logging.getLogger(__name__)

class DocumentEmbeddingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        logger.debug("Initialized DocumentEmbeddingsRepository with OpenAI embeddings model")
    
    def _create_vector_store(self, unique_identifier_project: str) -> PGVector:
        logger.debug(f"Creating vector store for collection: {unique_identifier_project}")
        return PGVector(
            embeddings=self.embeddings_model,
            collection_name=unique_identifier_project,
            connection=DATABASE_URL,
            pre_delete_collection=False,
            async_mode=True
        )
    
    def _get_unique_identifier(self, domain: str, project_key: str, internal_id: str) -> str:
        unique_id = f"{re.sub(r'^https?://|/$', '', domain)}/{project_key}/{internal_id}"
        logger.debug(f"Generated unique identifier: {unique_id}")
        return unique_id
    
    async def collection_exists(self, unique_identifier: str) -> bool:
        logger.debug(f"Checking if collection exists: {unique_identifier}")
        query = text("SELECT EXISTS (SELECT 1 FROM langchain_pg_collection WHERE name = :name)")
        result = await self.session.execute(query, {"name": unique_identifier})
        exists = result.scalar()
        logger.debug(f"Collection {unique_identifier} exists: {exists}")
        return exists
    
    async def delete_collection(self, domain: str, project_key: str, internal_id: str) -> None:
        unique_identifier = self._get_unique_identifier(domain, project_key, internal_id)
        logger.debug(f"Attempting to delete collection: {unique_identifier}")
        vector_store = self._create_vector_store(unique_identifier)
        await vector_store.adelete_collection()
        logger.info(f"Successfully deleted collection: {unique_identifier}")
    
    async def add_embeddings(self, 
                           domain: str,
                           project_key: str, 
                           internal_id: str,
                           documents: List[DocumentEmbedding],
                           batch_size: int = 100) -> None:
        unique_identifier = self._get_unique_identifier(domain, project_key, internal_id)
        logger.info(f"Creating new collection for {unique_identifier} and generating embeddings")
        vector_store = self._create_vector_store(unique_identifier)
        
        total_batches = (len(documents) + batch_size - 1) // batch_size
        logger.info(f"Processing {len(documents)} documents in {total_batches} batches")
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            current_batch = i // batch_size + 1
            logger.info(f"Processing batch {current_batch}/{total_batches}")
            
            embedding_texts = [doc.embedding_vector for doc in batch]
            metadatas = [{
                'ticket_url': doc.ticket_url,
                'issue_type': doc.issue_type,
                'status': doc.status,
                'priority': doc.priority,
                'sprint': doc.sprint,
                'key': doc.key,
                'labels': doc.labels,
                'resolution': doc.resolution,
                'parent': doc.parent,
                'assignee': doc.assignee,
                'reporter': doc.reporter,
                'resolutiondate': doc.resolutiondate.isoformat() if doc.resolutiondate else None,
                'created_at': doc.created_at.isoformat(),
                'updated_at': doc.updated_at.isoformat(),
            } for doc in batch]
            
            embeddings = await self.embeddings_model.aembed_documents(embedding_texts)
            logger.info(f"Generated {len(embeddings)} embeddings for batch {current_batch}")
            
            await vector_store.aadd_embeddings(
                texts=[""] * len(embeddings),  # We store the actual content in metadata
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully processed batch {current_batch}/{total_batches}")
        
        logger.info(f"Successfully completed processing all {len(documents)} documents")
