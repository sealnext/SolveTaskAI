import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from models import APIKey
from services import UserService, AuthService
from services.data_extractor import create_data_extractor
from dependencies import get_user_service, get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/all")
async def get_all_projects(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.get_current_user(request)
    api_keys = await user_service.get_api_keys_by_user(user)
    data_extractor = create_data_extractor(api_keys[0])
    data = await data_extractor.get_all_projects()

    projects = [
        {
            "name": project.get("name"),
            "key": project.get("key"),
            "id": project.get("id"),
            "avatarUrl": project.get("avatarUrls", {}).get("48x48"),  # Fallback to empty dict if avatarUrls is missing
            "projectTypeKey": project.get("projectTypeKey"),
            "style": project.get("style")
        }
        for project in data
    ]

    return projects
