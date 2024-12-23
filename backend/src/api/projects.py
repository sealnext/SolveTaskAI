import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from dependencies import (
    get_api_key_repository,
    get_project_service,
    get_user_service,
    get_document_embeddings_service
)
from exceptions import InvalidCredentialsException
from middleware.auth_middleware import auth_middleware
from repositories import APIKeyRepository
from schemas import APIKeySchema, ExternalProjectSchema, InternalProjectCreate, InternalProjectSchema
from services import ProjectService, UserService
from services.data_extractor import create_data_extractor
from models.document_embeddings import DocumentEmbeddingCreate
from services.document_embeddings_service import DocumentEmbeddingsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(auth_middleware)]
)

@router.post("/external", response_model=List[ExternalProjectSchema])
async def get_all_external_projects(
    api_key: APIKeySchema,
):
    data_extractor = create_data_extractor(api_key)
    projects = await data_extractor.get_all_projects()
    if not projects or projects == []:
        print("No projects found")
        raise InvalidCredentialsException
    return projects

@router.post("/external/id/{project_id}", response_model=List[ExternalProjectSchema])
async def get_external_project_by_id(
    request: Request,
    project_id: int,
    user_service: UserService = Depends(get_user_service)
):
    user = request.state.user
    api_key = await user_service.get_api_key_by_id(project_id, user.id)
    if not api_key:
        raise HTTPException(status_code=404, detail="Project not found")
    
    data_extractor = create_data_extractor(api_key)
    projects = await data_extractor.get_all_projects()
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
    3. Process and generate embeddings for project documents
    4. Return success/failure message with project details
    """
    # Step 1: Save project and get API key
    user_id = request.state.user.id
    new_project = await project_service.save_project(project, user_id)
    
    # Get and validate API key
    api_key = await api_key_repository.get_by_project_id(new_project.id)
    if not api_key:
        logger.error(f"No API key found for project {new_project.id}")
        raise HTTPException(status_code=404, detail="No API key found for project")
    
    # Step 2: Prepare embeddings request
    embeddings_request = DocumentEmbeddingCreate(
        project_id=new_project.id,
        project_key=new_project.key,
        domain=new_project.domain,
        internal_id=str(new_project.internal_id),
        api_key=api_key,  # Already an APIKeySchema
        action="add"
    )
    
    # Step 3: Process documents and generate embeddings
    processing_result = await embeddings_service.process_documents(embeddings_request)

    # Step 4: Return appropriate response based on processing result
    if processing_result["status"] == "success":
        processed_tickets_count = len(processing_result["tickets"])
        if processed_tickets_count > 0:
            return {
                "message": f"There are now {processed_tickets_count} tickets available in this project context.",
                "project_id": new_project.id
            }
    
    return {"message": processing_result["message"]}

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
    3. Check and clean up associated embeddings
    4. Return success response
    
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
        # Prepare embeddings deletion request
        embeddings_request = DocumentEmbeddingCreate(
            project_id=project.id,
            project_key=project.key,
            domain=project.domain,
            internal_id=str(project.internal_id),
            action="delete" 
        )
        
        try:
            # Delete embeddings from vector store
            deletion_result = await embeddings_service.process_documents(embeddings_request)
            if deletion_result["status"] != "success":
                error_msg = f"Failed to delete embeddings: {deletion_result}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail="Failed to delete embeddings")
            logger.info(f"Successfully deleted embeddings for project {external_project_id}")
        except Exception as e:
            error_msg = f"Error during embeddings deletion: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail="Failed to delete embeddings")

    # Step 4: Return success response
    return Response(status_code=204)
