from logging import getLogger
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request

from app.dependency import (
	get_api_key_repository,
	get_apikey_service,
	get_document_embeddings_service,
	get_project_service,
	get_ticketing_client_factory,
)
from app.dto.api_key import ApiKey
from app.dto.project import ExternalProject, ProjectCreate, ProjectResponse
from app.repository.api_key import ApiKeyRepository
from app.service.apikey import ApiKeyService
from app.service.document_embeddings import DocumentEmbeddingsService
from app.service.project import ProjectService
from app.service.ticketing.client import BaseTicketingClient
from app.service.ticketing.factory import TicketingClientFactory

logger = getLogger(__name__)

router = APIRouter()


@router.get(
	'/{api_key_id}/external', status_code=status.HTTP_200_OK, response_model=List[ExternalProject]
)
async def get_external_project_by_api_key(
	request: Request,
	api_key_id: int,
	api_key_service: ApiKeyService = Depends(get_apikey_service),
	factory: TicketingClientFactory = Depends(get_ticketing_client_factory),
) -> List[ExternalProject]:
	"""
	Get external projects (JIRA, AZURE, etc) for a specific api key.
	"""
	api_key: ApiKey = await api_key_service.get_api_key_unmasked(api_key_id, request.state.user_id)

	client: BaseTicketingClient = factory.get_client(api_key)
	projects: List[ExternalProject] = await client.get_projects()

	return projects


@router.post('/add', status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def add_internal_project(
	request: Request,
	project: ProjectCreate,
	project_service: ProjectService = Depends(get_project_service),
	api_key_repository: ApiKeyRepository = Depends(get_api_key_repository),
	embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service),
) -> ProjectResponse:
	"""
	Add and embed documents for a new project.
	"""
	user_id = request.state.user_id

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
	request: Request,
	project_service: ProjectService = Depends(get_project_service),
):
	"""
	Get all internal projects for the current user.
	"""
	projects = await project_service.get_all_for_user(request.state.user_id)
	return projects


@router.delete('/internal/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_internal_project(
	request: Request,
	project_id: int,
	project_service: ProjectService = Depends(get_project_service),
	embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service),
) -> None:
	"""
	Delete an internal project and its associated documents.
	"""
	user_id = request.state.user_id

	project = await project_service.get_project_by_id(user_id, project_id)
	project_was_deleted = await project_service.delete_project_by_id(user_id, project_id)

	if project_was_deleted:
		await embeddings_service.delete_documents(
			project.domain,
			project.key,
			project.external_id,
		)
