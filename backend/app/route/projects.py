import logging
from typing import List

from fastapi import APIRouter, Depends, Request, Response, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from app.dependencies import (
    get_api_key_repository,
    get_project_service,
    get_user_service,
    get_document_embeddings_service,
    get_ticketing_factory,
    get_apikey_service,
)
from app.repository.apikey_repository import APIKeyRepository
from app.schema.project import ExternalProject, ProjectCreate, Project
from app.schema.user import UserRead
from app.service.project_service import ProjectService
from app.service.user_service import UserService
from app.service.apikey_service import APIKeyService
from app.service.document_embeddings_service import DocumentEmbeddingsService
from app.service.ticketing.factory import TicketingClientFactory

import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/external/projects/{project_id}")
async def get_external_project_by_id(
    project_id: int,
    # user: User = Depends(get_current_user), # TODO AFTER AUTH REFACTOR
    request: Request,
    user_service: UserService = Depends(get_user_service),
    api_key_service: APIKeyService = Depends(get_apikey_service),
    project_service: ProjectService = Depends(get_project_service),
    factory: TicketingClientFactory = Depends(get_ticketing_factory),
) -> List[ExternalProject]:
    """
    Get external projects (JIRA, AZURE, etc) for a specific project ID.
    """
    # user = request.state.user
    user: UserRead = await user_service.get_user_by_email("ovidiubachmatchi@gmail.com")

    api_key, project = await asyncio.gather(
        api_key_service.get_api_key_for_project(user.id, project_id),
        project_service.get_project_by_id(user.id, project_id),
    )

    client = factory.get_client(api_key, project)
    projects = await client.get_projects()

    return projects


@router.post("/internal/add")
async def add_internal_project(
    project: ProjectCreate,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
    embeddings_service: DocumentEmbeddingsService = Depends(
        get_document_embeddings_service
    ),
) -> dict[str, str | int]:
    """Add a new internal project and process its documents for embeddings.

    Returns:
        dict: Success message and project ID on success
    """
    user_id = request.state.user.id

    new_project = await project_service.save_project(project, user_id)
    api_key = await api_key_repository.get_by_project_id(new_project.id)
    await embeddings_service.add_documents(
        domain=new_project.domain,
        project_key=new_project.key,
        internal_id=str(new_project.internal_id),
        api_key=api_key,
    )

    return {
        "message": "Project added successfully",
        "project_id": new_project.id,
    }


@router.get("/internal", response_model=List[Project])
async def get_all_internal_projects(
    request: Request, project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    projects = await project_service.get_all_for_user(user_id)
    return projects


async def _cleanup_project_embeddings(
    embeddings_service: DocumentEmbeddingsService,
    project: Project,
    external_project_id: int,
) -> None:
    """Clean up project embeddings from vector store."""
    try:
        await embeddings_service.delete_documents(
            domain=project.domain,
            project_key=project.key,
            internal_id=str(project.internal_id),
        )
        logger.info(
            f"Successfully deleted embeddings for project {external_project_id}"
        )
    except Exception as e:
        logger.error(f"Failed to delete embeddings: {str(e)}", exc_info=True)
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete embeddings"
        )


# TODO change this to use internal id
@router.delete("/internal/{external_project_id}")
async def delete_internal_project(
    external_project_id: int,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    embeddings_service: DocumentEmbeddingsService = Depends(
        get_document_embeddings_service
    ),
) -> Response:
    """Delete an internal project and its associated embeddings.

    Steps:
    1. Validate project existence and access
    2. Delete project from database
    3. Clean up embeddings from vector store

    Raises:
        ProjectNotFoundError: If project not found (404)
        DocumentProcessingException: If embeddings deletion fails (500)
    """
    user_id = request.state.user.id

    # Step 1: Validate project
    logger.info(f"Validating project {external_project_id}")
    project = await project_service.get_project_by_external_id(external_project_id)
    if not project:
        logger.error(f"Project {external_project_id} not found")
        raise HTTPException(HTTP_404_NOT_FOUND, "Project not found")

    try:
        # Step 2: Delete project
        logger.info(f"Deleting project {external_project_id}")
        await project_service.delete_project_by_external_id(
            user_id, external_project_id
        )

        # Step 3: Clean up embeddings
        has_embeddings = await project_service.delete_embeddings_by_external_id(
            user_id, external_project_id
        )
        if not has_embeddings:
            await _cleanup_project_embeddings(
                embeddings_service, project, external_project_id
            )

        return Response(status_code=204)

    except Exception as e:
        logger.error(f"Failed to delete project {external_project_id}: {str(e)}")
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete project resources"
        )
