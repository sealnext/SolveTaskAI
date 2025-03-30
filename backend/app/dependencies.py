# Standard library imports
from functools import cache

# Third-party imports
from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.misc.database.pool import db_pool
from app.misc.database.postgres import get_db
from app.repository.apikey_repository import APIKeyRepository
from app.repository.chat_session_repository import ChatSessionRepository
from app.repository.project_repository import ProjectRepository
from app.repository.document_embeddings_repository import DocumentEmbeddingsRepository
from app.repository.thread_repository import ThreadRepository
from app.repository.user_repository import UserRepository
from app.schema.api_key import APIKey
from app.service.apikey_service import APIKeyService
from app.service.document_embeddings_service import DocumentEmbeddingsService
from app.service.project_service import ProjectService
from app.service.ticketing.factory import TicketingClientFactory
from app.service.user_service import UserService
from app.service.ticketing.client import BaseTicketingClient
from app.service.ticketing.factory import TicketingConfig


# User dependencies
async def get_api_key_repository(db: AsyncSession = Depends(get_db)):
    return APIKeyRepository(db_session=db)


async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)


async def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
):
    return UserService(repo, api_key_repo)


# Project dependencies
async def get_project_repository(db: AsyncSession = Depends(get_db)):
    return ProjectRepository(db)


async def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    return ProjectService(project_repo)


async def get_apikey_service(repo: APIKeyRepository = Depends(get_api_key_repository)):
    return APIKeyService(repo)


async def get_chat_session_repository(db: AsyncSession = Depends(get_db)):
    return ChatSessionRepository(db)


# Checkpointer dependency
async def get_db_checkpointer() -> AsyncPostgresSaver:
    """FastAPI dependency for getting the checkpointer."""
    if db_pool.checkpointer is None:
        await db_pool.create_pool()
    return db_pool.checkpointer


# Thread Repository
async def get_thread_repository(db: AsyncSession = Depends(get_db)) -> ThreadRepository:
    """Get thread repository."""
    return ThreadRepository(db)


# Ticketing System dependencies
@cache
def get_ticketing_factory() -> TicketingClientFactory:
    """Get the ticketing factory singleton."""
    return TicketingClientFactory(config=TicketingConfig())


def get_ticketing_client(
    api_key: APIKey, factory: TicketingClientFactory = Depends(get_ticketing_factory)
) -> BaseTicketingClient:
    """Get a ticketing client with connection pooling."""
    return factory.get_client(api_key)


# Document Embeddings dependencies
async def get_document_embeddings_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentEmbeddingsRepository:
    """Get document embeddings repository."""
    return DocumentEmbeddingsRepository(db)


async def get_document_embeddings_service(
    repository: DocumentEmbeddingsRepository = Depends(
        get_document_embeddings_repository
    ),
    factory: TicketingClientFactory = Depends(get_ticketing_factory),
) -> DocumentEmbeddingsService:
    """Get document embeddings service with proper dependency injection."""
    return DocumentEmbeddingsService(repository=repository, factory=factory)
