import logging
from fastapi import APIRouter, Depends, Request
from typing import List

from services.data_extractor import create_data_extractor
from validation_models import ExternalProjectSchema, APIKeySchema, InternalProjectSchema
from middleware.auth_middleware import auth_middleware
from services import ProjectService
from dependencies import get_project_service
from exceptions import InvalidCredentialsException

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

@router.get("/internal", response_model=List[InternalProjectSchema])
async def get_all_internal_projects(
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    user_id = request.state.user.id
    projects = await project_service.get_all_for_user(user_id)
    return projects
