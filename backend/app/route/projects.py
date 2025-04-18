from logging import getLogger
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependency import (
	get_api_key_repository,
	get_apikey_service,
	get_document_embeddings_service,
	get_project_service,
	get_ticketing_client_factory,
	get_user_service,
)
from app.dto.api_key import ApiKey
from app.dto.project import ExternalProject, ProjectCreate, ProjectResponse
from app.repository.api_key import ApiKeyRepository
from app.service.apikey import ApiKeyService
from app.service.document_embeddings import DocumentEmbeddingsService
from app.service.project import ProjectService
from app.service.ticketing.client import BaseTicketingClient
from app.service.ticketing.factory import TicketingClientFactory
from app.service.user import UserService

logger = getLogger(__name__)

router = APIRouter(prefix='/project', tags=['projects'])


@router.get(
	'/{api_key_id}/external', status_code=status.HTTP_200_OK, response_model=List[ExternalProject]
)
async def get_external_project_by_api_key(
	api_key_id: int,
	user_service: UserService = Depends(get_user_service),
	api_key_service: ApiKeyService = Depends(get_apikey_service),
	factory: TicketingClientFactory = Depends(get_ticketing_client_factory),
) -> List[ExternalProject]:
	"""
	Get external projects (JIRA, AZURE, etc) for a specific api key.
	"""
	# TODO AFTER AUTH REFACTOR
	user_id = 0
	api_key: ApiKey = await api_key_service.get_api_key_by_id_and_user(api_key_id, user_id)

	client: BaseTicketingClient = factory.get_client(api_key)
	projects: List[ExternalProject] = await client.get_projects()

	return projects


@router.post('/add', status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def add_internal_project(
	project: ProjectCreate,
	project_service: ProjectService = Depends(get_project_service),
	user_service: UserService = Depends(get_user_service),
	api_key_repository: ApiKeyRepository = Depends(get_api_key_repository),
	embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service),
) -> ProjectResponse:
	"""
	Add and embed documents for a new project.
	"""
	# TODO AFTER AUTH REFACTOR
	user_id = 0
	api_key: ApiKey | None = await api_key_repository.get_by_id_and_user(
		project.api_key_id, user_id
	)
	if api_key is None:
		raise HTTPException(status.HTTP_404_NOT_FOUND, 'API key not found')

	new_project, is_new_project = await project_service.save_project(project, user_id, api_key)

	if is_new_project:
		await embeddings_service.add_documents(
			domain=project.domain,
			project_key=project.key,
			external_id=project.external_id,
			api_key=api_key,
		)

	return new_project


@router.get('/internal', status_code=status.HTTP_200_OK, response_model=List[ProjectResponse])
async def get_all_internal_projects(
	project_service: ProjectService = Depends(get_project_service),
	user_service: UserService = Depends(get_user_service),
):
	"""
	Get all internal projects for the current user.
	"""
	# TODO AFTER AUTH REFACTOR
	user_id = 0
	projects = await project_service.get_all_for_user(user_id)
	return projects


@router.delete('/internal/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_internal_project(
	project_id: int,
	project_service: ProjectService = Depends(get_project_service),
	embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service),
	user_service: UserService = Depends(get_user_service),
) -> None:
	"""
	Delete an internal project and its associated documents.
	"""
	# TODO AFTER AUTH REFACTOR
	user_id = 0
	project = await project_service.get_project_by_id(user_id, project_id)

	project_was_deleted = await project_service.delete_project_by_id(user_id, project_id)

	if project_was_deleted:
		await embeddings_service.delete_documents(
			domain=project.domain,
			project_key=project.key,
			external_id=str(project.external_id),
		)
