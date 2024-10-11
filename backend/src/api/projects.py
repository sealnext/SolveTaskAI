import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from models import APIKey

from services.data_extractor import create_data_extractor
from services import UserService

from dependencies import get_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/all")
async def get_all_projects(request: Request, user_service: UserService = Depends(get_user_service)):
    user = await user_service.get_current_user(request)
    print("user", user)
    api_keys = await user_service.get_api_keys_by_user(user)
    print("api_keys", api_keys)
    data_extractor = create_data_extractor(api_keys[0])
    data = await data_extractor.get_all_projects()
    print("data", data)
    return data
