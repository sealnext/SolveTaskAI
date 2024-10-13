from fastapi import APIRouter, Depends, Request
from middleware.auth_middleware import auth_middleware
from dependencies import get_user_service
from services import UserService


router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
    dependencies=[Depends(auth_middleware)]
)

@router.get("/")
async def retrieve_api_keys(
    request: Request, 
    user_service: UserService = Depends(get_user_service)
):
    user = request.state.user
    api_keys = await user_service.get_api_keys_by_user(user)
    return {"message": "API keys retrieved successfully", "data": api_keys}
