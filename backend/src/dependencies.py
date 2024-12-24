# Standard library imports
from functools import lru_cache

# Third-party imports
from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from db.pool import db_pool
from db.session import get_db
from repositories import (
    APIKeyRepository,
    ChatSessionRepository,
    ProjectRepository
)
from repositories.document_embeddings_repository import DocumentEmbeddingsRepository
from repositories.thread_repository import ThreadRepository
from repositories.user_repository import UserRepository
from schemas import APIKeySchema
from services import (
    APIKeyService,
    AuthService,
    DocumentEmbeddingsService,
    ProjectService,
    TicketingClientFactory,
    UserService
)
from services.ticketing import BaseTicketingClient
from services.ticketing.factory import TicketingConfig

# User dependencies
async def get_api_key_repository(db: AsyncSession = Depends(get_db)):
    return APIKeyRepository(db_session=db)

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

async def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository)
):
    return UserService(repo, api_key_repo)

async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)):
    return AuthService(user_repo)

# Project dependencies
async def get_project_repository(db: AsyncSession = Depends(get_db)):
    return ProjectRepository(db)

async def get_project_service(project_repo: ProjectRepository = Depends(get_project_repository)):
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
@lru_cache()
def get_ticketing_factory() -> TicketingClientFactory:
    """Get the ticketing factory singleton."""
    return TicketingClientFactory(config=TicketingConfig())

def get_ticketing_client(
    api_key: APIKeySchema,
    factory: TicketingClientFactory = Depends(get_ticketing_factory)
) -> BaseTicketingClient:
    """Get a ticketing client with connection pooling."""
    return factory.get_client(api_key)

# Document Embeddings dependencies
async def get_document_embeddings_repository(db: AsyncSession = Depends(get_db)) -> DocumentEmbeddingsRepository:
    """Get document embeddings repository."""
    return DocumentEmbeddingsRepository(db)

async def get_document_embeddings_service(
    repository: DocumentEmbeddingsRepository = Depends(get_document_embeddings_repository),
    factory: TicketingClientFactory = Depends(get_ticketing_factory)
) -> DocumentEmbeddingsService:
    """Get document embeddings service with proper dependency injection."""
    return DocumentEmbeddingsService(
        repository=repository,
        factory=factory
    )