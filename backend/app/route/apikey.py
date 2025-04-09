from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_apikey_service, get_user_service
from app.dto.api_key import APIKeyCreate
from app.service.apikey_service import APIKeyService
from app.service.user_service import UserService

router = APIRouter(prefix='/api-keys', tags=['api-keys'])


@router.get('/')
async def retrieve_api_keys(
	request: Request, user_service: UserService = Depends(get_user_service)
):
	user = request.state.user
	api_keys = await user_service.get_api_keys_by_user(user)
	return {'message': 'API keys retrieved successfully', 'data': api_keys}


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_api_key(
	api_key_data: APIKeyCreate,
	request: Request,
	apikey_service: APIKeyService = Depends(get_apikey_service),
):
	user = request.state.user
	new_api_key = await apikey_service.create_api_key(user.id, api_key_data)
	return {'message': 'API key added successfully', 'data': new_api_key}


@router.delete('/{api_key_id}')
async def delete_api_key(
	api_key_id: int,
	request: Request,
	apikey_service: APIKeyService = Depends(get_apikey_service),
):
	user = request.state.user
	await apikey_service.delete_api_key(user.id, api_key_id)
	return {'message': 'API key deleted successfully'}
