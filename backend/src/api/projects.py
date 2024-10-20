import logging
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from typing import List
from fastapi.responses import JSONResponse

from services.data_extractor import create_data_extractor
from schemas import ExternalProjectSchema, APIKeySchema, InternalProjectSchema, InternalProjectCreate
from middleware.auth_middleware import auth_middleware
from services import ProjectService
from dependencies import get_project_service
from exceptions import InvalidCredentialsException
from services import UserService
from dependencies import get_user_service

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

@router.post("/internal/add", response_model=InternalProjectSchema)
async def add_internal_project(
    project: InternalProjectCreate,
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    new_project = await project_service.save_project(project, user_id)
    return new_project

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
