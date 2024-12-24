import logging
from typing import List, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from dependencies import (
    get_api_key_repository,
    get_project_service,
    get_user_service,
    get_document_embeddings_service,
    get_ticketing_client,
    get_ticketing_factory
)
from exceptions import InvalidCredentialsException
from middleware.auth_middleware import auth_middleware
from repositories import APIKeyRepository
from schemas import APIKeySchema, ExternalProjectSchema, InternalProjectCreate, InternalProjectSchema
from services import ProjectService, UserService, DocumentEmbeddingsService, TicketingClientFactory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(auth_middleware)]
)

@router.post("/external")
async def get_all_external_projects(
    api_key: APIKeySchema,
    ticketing_client: Callable = Depends(get_ticketing_client)
) -> List[ExternalProjectSchema]:
    """Get all external projects for an API key."""
    client = ticketing_client(api_key)
    projects = await client.get_projects(api_key)
    if not projects:
        logger.warning("No projects found")
        raise InvalidCredentialsException
    return projects

@router.get("/external/id/{project_id}")
async def get_external_project_by_id(
    project_id: int,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    factory: TicketingClientFactory = Depends(get_ticketing_factory)
) -> List[ExternalProjectSchema]:
    """Get external projects for a specific project ID."""
    user = request.state.user
    api_key = await user_service.get_api_key_by_id(project_id, user.id)
    if not api_key:
        raise HTTPException(status_code=404, detail="Project not found")
    
    api_key_schema = APIKeySchema.from_orm(api_key)
    logger.info(f"API Key Schema: {api_key_schema}")
    client = factory.get_client(api_key_schema)
    projects = await client.get_projects(api_key_schema)
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found in external service. Check your API Key.")
    return projects

@router.post("/internal/add")
async def add_internal_project(
    project: InternalProjectCreate,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
    embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service)
) -> dict:
    """Add a new internal project and process its documents for embeddings.
    
    Steps:
    1. Save the project in the database
    2. Get the API key for the project
    3. Add documents to the embeddings repository
    """
    try:
        # Step 1: Save project and get API key
        user_id = request.state.user.id
        new_project = await project_service.save_project(project, user_id)
        
        # Get and validate API key
        api_key = await api_key_repository.get_by_project_id(new_project.id)
        if not api_key:
            logger.error(f"No API key found for project {new_project.id}")
            await project_service.delete_project_by_external_id(user_id, new_project.internal_id)
            raise HTTPException(status_code=404, detail="No API key found for project")
        
        # Step 2: Process documents and generate embeddings
        try:
            await embeddings_service.add_documents(
                domain=new_project.domain,
                project_key=new_project.key,
                internal_id=str(new_project.internal_id),
                api_key=api_key
            )
            return {
                "message": "Project added successfully. You can now start chatting with your project.",
                "project_id": new_project.id
            }
        except ValueError as e:
            # If no documents found, delete the project and return error
            logger.warning(f"No documents found for project: {str(e)}")
            await project_service.delete_project_by_external_id(user_id, new_project.internal_id)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # For other errors, delete project and re-raise
            logger.error(f"Error processing documents: {str(e)}")
            await project_service.delete_project_by_external_id(user_id, new_project.internal_id)
            raise HTTPException(status_code=500, detail="Failed to process documents")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/internal", response_model=List[InternalProjectSchema])
async def get_all_internal_projects(
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    projects = await project_service.get_all_for_user(user_id)
    return projects

#TODO change this to use internal id
@router.delete("/internal/{external_project_id}")
async def delete_internal_project(
    external_project_id: int,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    embeddings_service: DocumentEmbeddingsService = Depends(get_document_embeddings_service)
) -> Response:
    """Delete an internal project and its associated embeddings.
    
    Steps:
    1. Validate project existence and access
    2. Delete project from database
    3. Delete embeddings from vector store
    
    Raises:
        HTTPException: If project not found (404) or embeddings deletion fails (500)
    """
    # Step 1: Validate project existence
    user_id = request.state.user.id
    project = await project_service.get_project_by_external_id(external_project_id)
    if not project:
        logger.error(f"Project not found with external ID: {external_project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    # Step 2: Delete project from database
    logger.info(f"Deleting project with external ID: {external_project_id}")
    await project_service.delete_project_by_external_id(user_id, external_project_id)
    
    # Step 3: Clean up associated embeddings if necessary
    has_embeddings = await project_service.delete_embeddings_by_external_id(user_id, external_project_id)
    logger.debug(f"Project has embeddings to clean up: {not has_embeddings}")
    
    if not has_embeddings:
        try:
            # Delete embeddings from vector store
            await embeddings_service.delete_documents(
                domain=project.domain,
                project_key=project.key,
                internal_id=str(project.internal_id)
            )
            logger.info(f"Successfully deleted embeddings for project {external_project_id}")
        except Exception as e:
            error_msg = f"Error during embeddings deletion: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail="Failed to delete embeddings")

    # Step 4: Return success response
    return Response(status_code=204)
