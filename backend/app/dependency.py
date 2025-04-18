from functools import cache
from typing import Annotated

from fastapi import Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.api_key import ApiKey
from app.misc.pool import db_pool
from app.misc.postgres import get_async_db_session
from app.repository.api_key import ApiKeyRepository
from app.repository.document_embeddings import DocumentEmbeddingsRepository
from app.repository.project import ProjectRepository
from app.repository.thread import ThreadRepository
from app.repository.user import UserRepository
from app.service.apikey import ApiKeyService
from app.service.auth import AuthService
from app.service.document_embeddings import DocumentEmbeddingsService
from app.service.project import ProjectService
from app.service.ticketing.client import BaseTicketingClient
from app.service.ticketing.factory import TicketingClientFactory, TicketingConfig
from app.service.user import UserService

""" Core dependencies """

AsyncDbSessionDep = Annotated[AsyncSession, Depends(get_async_db_session)]


def get_db_checkpointer() -> AsyncPostgresSaver:
	return db_pool.get_checkpointer()


DbCheckpointerDep = Annotated[AsyncPostgresSaver, Depends(get_db_checkpointer)]


@cache
def get_ticketing_client_factory() -> TicketingClientFactory:
	"""Get the ticketing factory singleton."""
	return TicketingClientFactory(config=TicketingConfig())


TicketingClientFactoryDep = Annotated[TicketingClientFactory, Depends(get_ticketing_client_factory)]


def get_ticketing_client(
	api_key: ApiKey, factory: TicketingClientFactoryDep
) -> BaseTicketingClient:
	"""Get a ticketing client with connection pooling."""
	return factory.get_client(api_key)


TicketingClientDep = Annotated[BaseTicketingClient, Depends(get_ticketing_client)]


""" Repositories """


def get_api_key_repository(
	db_session: AsyncDbSessionDep,
) -> ApiKeyRepository:
	return ApiKeyRepository(db_session)


ApiKeyRepositoryDep = Annotated[ApiKeyRepository, Depends(get_api_key_repository)]


def get_user_repository(
	db_session: AsyncDbSessionDep,
) -> UserRepository:
	return UserRepository(db_session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_project_repository(
	db_session: AsyncDbSessionDep,
) -> ProjectRepository:
	return ProjectRepository(db_session)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_thread_repository(db_session: AsyncDbSessionDep) -> ThreadRepository:
	"""Get thread repository."""
	return ThreadRepository(db_session)


ThreadRepositoryDep = Annotated[ThreadRepository, Depends(get_thread_repository)]


def get_document_embeddings_repository(
	db_session: AsyncDbSessionDep,
) -> DocumentEmbeddingsRepository:
	"""Get document embeddings repository."""
	return DocumentEmbeddingsRepository(db_session)


DocumentEmbeddingsRepositoryDep = Annotated[
	DocumentEmbeddingsRepository, Depends(get_document_embeddings_repository)
]

""" Services """


def get_user_service(
	user_repository: UserRepositoryDep,
) -> UserService:
	return UserService(user_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(user_service: UserServiceDep) -> AuthService:
	return AuthService(user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_project_service(
	project_repository: ProjectRepositoryDep,
) -> ProjectService:
	return ProjectService(project_repository)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_apikey_service(
	api_key_repository: ApiKeyRepositoryDep,
) -> ApiKeyService:
	return ApiKeyService(api_key_repository)


ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_apikey_service)]


def get_document_embeddings_service(
	document_embeddings_repository: DocumentEmbeddingsRepositoryDep,
	ticketing_client_factory: TicketingClientFactoryDep,
) -> DocumentEmbeddingsService:
	"""Get document embeddings service with proper dependency injection."""
	return DocumentEmbeddingsService(document_embeddings_repository, ticketing_client_factory)


DocumentEmbeddingsServiceDep = Annotated[
	DocumentEmbeddingsService, Depends(get_document_embeddings_service)
]
