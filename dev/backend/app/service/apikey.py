from logging import getLogger
from typing import List

from fastapi import HTTPException, status

from app.dto.api_key import ApiKey, ApiKeyCreate, ApiKeyResponse
from app.misc.crypto import decrypt, encrypt
from app.model.api_key import ApiKeyDB
from app.repository.api_key import ApiKeyRepository

logger = getLogger(__name__)


class ApiKeyService:
	def __init__(self, apikey_repository: ApiKeyRepository):
		self.apikey_repository = apikey_repository

	async def add_api_key(self, user_id: int, api_key_data: ApiKeyCreate) -> ApiKeyResponse:
		encrypted_key = encrypt(api_key_data.api_key)
		existing_key = await self.apikey_repository.get_by_value(encrypted_key)
		if existing_key:
			raise HTTPException(
				status.HTTP_409_CONFLICT,
				'An API key with this value already exists.',
			)

		try:
			api_key_data.api_key = encrypted_key
			created_key: ApiKeyDB = await self.apikey_repository.create_api_key(
				user_id, api_key_data
			)
		except Exception as e:
			logger.error(f'Failed to create API key: {e}')
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				'Failed to create API key due to an internal error.',
			)

		return ApiKeyResponse.model_validate(created_key)

	async def get_api_keys(self, user_id: int) -> List[ApiKeyResponse]:
		"""Get all API keys for a user with masked key values."""
		api_keys: List[ApiKeyDB] = await self.apikey_repository.get_api_keys_by_user(user_id)
		result = []
		for key in api_keys:
			key_dto = ApiKeyResponse.model_validate(key)
			key_dto.api_key = decrypt(key.api_key)
			result.append(key_dto)
		return result

	async def delete_api_key(self, user_id: int, api_key_id: int) -> None:
		key_to_delete: ApiKeyDB | None = await self.apikey_repository.get_by_id(api_key_id)

		if not key_to_delete:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'API Key not found.')

		if not hasattr(key_to_delete, 'user_id') or key_to_delete.user_id != user_id:
			raise HTTPException(
				status.HTTP_403_FORBIDDEN,
				'User does not have permission to delete this API Key.',
			)

		deleted = await self.apikey_repository.delete_api_key(api_key_id)

		if not deleted:
			logger.warning(
				f'Failed to delete API key {api_key_id} after ownership check for user {user_id}.'
			)
			raise HTTPException(
				status.HTTP_404_NOT_FOUND,
				'API Key could not be deleted or was already removed.',
			)
		logger.info(f'API key {api_key_id} deleted successfully by user {user_id}.')

	async def get_api_key_unmasked(self, api_key_id: int, user_id: int) -> ApiKey:
		"""Get an API key by ID with unmasked key value. Use with caution."""
		api_key_data: ApiKey | None = await self.apikey_repository.get_by_id_and_user(
			api_key_id, user_id
		)
		if not api_key_data:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'API Key not found.')

		api_key_dto = ApiKey.model_validate(api_key_data)
		api_key_dto.api_key = decrypt(api_key_data.api_key)
		return api_key_dto

	async def get_api_key_by_project_unmasked(self, user_id: int, project_id: int) -> ApiKey:
		api_key_data: ApiKeyDB | None = await self.apikey_repository.get_api_key_by_project(
			user_id, project_id
		)
		if not api_key_data:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'API Key not found.')

		api_key_dto = ApiKey.model_validate(api_key_data)
		api_key_dto.api_key = decrypt(api_key_data.api_key)
		return api_key_dto
