import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from dependencies import get_api_key_repository, get_project_service, get_user_service
from exceptions import InvalidCredentialsException
from middleware.auth_middleware import auth_middleware
from repositories import APIKeyRepository
from schemas import APIKeySchema, ExternalProjectSchema, InternalProjectCreate, InternalProjectSchema
from services import ProjectService, UserService
from services.data_extractor import create_data_extractor
from services.agent_service import process_documents

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
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository)
):
    user_id = request.state.user.id
    new_project = await project_service.save_project(project, user_id)
    api_key = await api_key_repository.get_by_project_id(new_project.id)
    
    initial_state = {
        "question": "",
        "project": new_project,
        "api_key": api_key,
        "user_id": user_id,
        "generation": "",
        "max_retries": 3,
        "answers": 0,
        "loop_step": 0,
        "documents": [],
        "tickets": []
    }
    
    final_state = await process_documents(
        initial_state
    )
    
    logger.info(f"Final state: {final_state}")
    
    tickets = len(final_state['tickets'])
    
    if tickets > 0:
        return {"message": f"There are now {tickets} tickets available in this project context.", "project_id": new_project.id}
    
    return {"message": final_state["status"]}

@router.get("/internal", response_model=List[InternalProjectSchema])
async def get_all_internal_projects(
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    projects = await project_service.get_all_for_user(user_id)
    return projects

@router.delete("/internal/{external_project_id}")
async def delete_internal_project(
    external_project_id: int,
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    await project_service.delete_project_by_external_id(user_id, external_project_id)
    return Response(status_code=204)
