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
from app.schema.api_key import APIKey
from app.service.project_service import ProjectService
from app.service.ticketing.client import BaseTicketingClient
from app.service.user_service import UserService
from app.service.apikey_service import APIKeyService
from app.service.document_embeddings_service import DocumentEmbeddingsService
from app.service.ticketing.factory import TicketingClientFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/project", tags=["projects"])


@router.get("/{api_key_id}/external")
async def get_external_project_by_api_key(
    api_key_id: int,
    user_service: UserService = Depends(get_user_service),
    api_key_service: APIKeyService = Depends(get_apikey_service),
    factory: TicketingClientFactory = Depends(get_ticketing_factory),
) -> List[ExternalProject]:
    """
    Get external projects (JIRA, AZURE, etc) for a specific api key.
    """
    # TODO AFTER AUTH REFACTOR
    # user = request.state.user
    user: UserRead = await user_service.get_user_by_email("ovidiubachmatchi@gmail.com")

    api_key: APIKey = await api_key_service.get_api_key_by_id_and_user(
        api_key_id, user.id
    )

    client: BaseTicketingClient = factory.get_client(api_key)
    projects: List[ExternalProject] = await client.get_projects()

    return projects


@router.post("/add")
async def add_internal_project(
    project: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service),
    user_service: UserService = Depends(get_user_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
    embeddings_service: DocumentEmbeddingsService = Depends(
        get_document_embeddings_service
    ),
) -> dict[str, str | int]:
    """
    Ingest and index an external project into the system.

    This endpoint creates a new internal project entry, associates it with the provided project details,
    and processes its documents to generate embeddings for efficient retrieval when querying with the project context.

    Returns:
        dict: A success message and the ID of the newly created project.
    """
    # TODO AFTER AUTH REFACTOR
    # user = request.state.user
    user: UserRead = await user_service.get_user_by_email("ovidiubachmatchi@gmail.com")

    api_key: APIKey = await api_key_repository.get_by_id_and_user(
        project.api_key_id, user.id
    )
    if not api_key:
        raise HTTPException(HTTP_404_NOT_FOUND, "API key not found")

    new_project: Project = await project_service.save_project(project, user.id)

    # TODO Streaming status updates to the client along with percentage completion as this could take a while
    await embeddings_service.add_documents(
        domain=new_project.domain,
        project_key=new_project.key,
        external_id=str(new_project.external_id),
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
        # Call the service delete method, which returns True if the project record itself was deleted
        project_was_deleted = await project_service.delete_project_by_external_id(
            user_id, external_project_id
        )

        # Step 3: If the project record was deleted, clean up embeddings
        if project_was_deleted:
            logger.info(
                f"Project record {external_project_id} deleted, cleaning up embeddings."
            )
            # Use the 'project' variable fetched earlier for details
            try:
                await embeddings_service.delete_documents(
                    domain=project.domain,
                    project_key=project.key,
                    external_id=str(project.external_id),
                )
                logger.info(
                    f"Successfully deleted embeddings for project {external_project_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to delete embeddings for project {external_project_id} after DB deletion: {str(e)}",
                    exc_info=True,
                )
                # Raise an error because the cleanup failed, even though DB deletion succeeded
                raise HTTPException(
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "Project deleted from DB, but failed to delete embeddings",
                ) from e
        else:
            logger.info(
                f"User {user_id} unlinked from project {external_project_id}. Embeddings not deleted."
            )

        return Response(status_code=204)

    except Exception as e:
        logger.error(f"Failed to delete project {external_project_id}: {str(e)}")
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete project resources"
        )
