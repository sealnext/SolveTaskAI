from fastapi import HTTPException, status
from typing import List

from app.repository.apikey_repository import APIKeyRepository
from app.schema.api_key import APIKeyCreate, APIKeyResponse, APIKey


class APIKeyService:
    def __init__(self, apikey_repository: APIKeyRepository):
        self.apikey_repository = apikey_repository

    async def create_api_key(
        self, user_id: int, api_key_data: APIKeyCreate
    ) -> APIKeyResponse:
        existing_key = await self.apikey_repository.get_by_value(
            api_key_data.api_key
        )
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An API key with this value already exists",
            )

        try:
            created_key: APIKey = await self.apikey_repository.create_api_key(
                user_id=user_id,
                api_key_value=api_key_data.api_key,
                service_type=api_key_data.service_type,
                domain=api_key_data.domain,
                domain_email=api_key_data.domain_email,
                project_ids=getattr(api_key_data, 'project_ids', []),
                permissions=getattr(api_key_data, 'permissions', None),
                expires_at=getattr(api_key_data, 'expires_at', None),
            )
        except Exception as e:
             # TODO: Replace print with proper logging
             print(f"Error creating API key: {e}") # Keeping the TODO and print for now as it seems intentional
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Failed to create API key."
             )

        return APIKeyResponse.model_validate(created_key)

    async def get_api_keys_by_user(self, user_id: int) -> List[APIKeyResponse]:
        api_keys: List[APIKey] = await self.apikey_repository.get_api_keys_by_user(user_id)
        return [APIKeyResponse.model_validate(key) for key in api_keys]

    async def delete_api_key(self, user_id: int, api_key_id: int) -> None:
        key_to_delete = await self.apikey_repository.get_by_id(api_key_id)

        if not key_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found"
            )

        if getattr(key_to_delete, 'user_id', None) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this API Key",
            )

        deleted = await self.apikey_repository.delete_api_key(api_key_id)

        if not deleted:
             # Handle potential race condition where key was deleted between check and call
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="API Key not found or could not be deleted.",
             )
