from fastapi import APIRouter, Depends, Request
from app.middleware.auth_middleware import auth_middleware
from app.dependencies import get_user_service, get_apikey_service
from app.services.user_service import UserService
from app.services.apikey_service import APIKeyService
from app.schemas.api_key import APIKeyCreate


router = APIRouter(
    prefix="/api-keys", tags=["api-keys"], dependencies=[Depends(auth_middleware)]
)


@router.get("/")
async def retrieve_api_keys(
    request: Request, user_service: UserService = Depends(get_user_service)
):
    user = request.state.user
    api_keys = await user_service.get_api_keys_by_user(user)
    return {"message": "API keys retrieved successfully", "data": api_keys}


@router.post("/add", status_code=201)
async def add_api_key(
    api_key_data: APIKeyCreate,
    request: Request,
    apikey_service: APIKeyService = Depends(get_apikey_service),
):
    user = request.state.user
    new_api_key = await apikey_service.create_api_key(user.id, api_key_data)
    return {"message": "API key added successfully", "data": new_api_key}


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    request: Request,
    apikey_service: APIKeyService = Depends(get_apikey_service),
):
    user = request.state.user
    await apikey_service.delete_api_key(user.id, api_key_id)
    return {"message": "API key deleted successfully"}
