from functools import cache

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.misc.database.pool import db_pool
from app.misc.database.postgres import get_db_session
from app.repository.apikey_repository import APIKeyRepository
from app.repository.document_embeddings_repository import DocumentEmbeddingsRepository
from app.repository.project_repository import ProjectRepository
from app.repository.thread_repository import ThreadRepository
from app.repository.user_repository import UserRepository
from app.schema.api_key import APIKey
from app.service.apikey_service import APIKeyService
from app.service.document_embeddings_service import DocumentEmbeddingsService
from app.service.project_service import ProjectService
from app.service.ticketing.client import BaseTicketingClient
from app.service.ticketing.factory import TicketingClientFactory, TicketingConfig
from app.service.user_service import UserService


def get_api_key_repository(
	db_session: AsyncSession = Depends(get_db_session),
) -> APIKeyRepository:
	return APIKeyRepository(db_session)


def get_user_repository(
	db_session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
	return UserRepository(db_session)


def get_user_service(
	user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
	return UserService(user_repository)


def get_project_repository(
	db_session: AsyncSession = Depends(get_db_session),
) -> ProjectRepository:
	return ProjectRepository(db_session)


def get_project_service(
	project_repository: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
	return ProjectService(project_repository)


def get_apikey_service(
	api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
) -> APIKeyService:
	return APIKeyService(api_key_repository)


def get_db_checkpointer() -> AsyncPostgresSaver:
	return db_pool.get_checkpointer()


def get_thread_repository(
	db_session: AsyncSession = Depends(get_db_session),
) -> ThreadRepository:
	"""Get thread repository."""
	return ThreadRepository(db_session)


@cache
def get_ticketing_factory() -> TicketingClientFactory:
	"""Get the ticketing factory singleton."""
	return TicketingClientFactory(config=TicketingConfig())


def get_ticketing_client(
	api_key: APIKey, factory: TicketingClientFactory = Depends(get_ticketing_factory)
) -> BaseTicketingClient:
	"""Get a ticketing client with connection pooling."""
	return factory.get_client(api_key)


def get_document_embeddings_repository(
	db_session: AsyncSession = Depends(get_db_session),
) -> DocumentEmbeddingsRepository:
	"""Get document embeddings repository."""
	return DocumentEmbeddingsRepository(db_session)


def get_document_embeddings_service(
	document_embeddings_repository: DocumentEmbeddingsRepository = Depends(
		get_document_embeddings_repository
	),
	ticketing_client_factory: TicketingClientFactory = Depends(get_ticketing_factory),
) -> DocumentEmbeddingsService:
	"""Get document embeddings service with proper dependency injection."""
	return DocumentEmbeddingsService(document_embeddings_repository, ticketing_client_factory)
