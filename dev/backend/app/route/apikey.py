from fastapi import APIRouter, Depends, Request, status

from app.dependency import get_apikey_service
from app.dto.api_key import ApiKeyCreate, ApiKeyResponse
from app.service.apikey import ApiKeyService

router = APIRouter()


@router.get('/', response_model=list[ApiKeyResponse], status_code=status.HTTP_200_OK)
async def retrieve_api_keys(
	request: Request, apikey_service: ApiKeyService = Depends(get_apikey_service)
):
	api_keys = await apikey_service.get_api_keys(request.state.user_id)
	return api_keys


@router.post('/add', response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_api_key(
	api_key_data: ApiKeyCreate,
	request: Request,
	apikey_service: ApiKeyService = Depends(get_apikey_service),
):
	new_api_key = await apikey_service.add_api_key(request.state.user_id, api_key_data)
	return new_api_key


@router.delete('/{api_key_id}')
async def delete_api_key(
	api_key_id: int,
	request: Request,
	apikey_service: ApiKeyService = Depends(get_apikey_service),
):
	await apikey_service.delete_api_key(request.state.user_id, api_key_id)
	return {'status': 'success'}
