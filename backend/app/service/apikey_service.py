import logging
from datetime import datetime, UTC
from typing import List

from fastapi import HTTPException, status

from app.model.api_key import APIKeyDB
from app.repository.apikey_repository import APIKeyRepository
from app.schema.api_key import APIKey, APIKeyCreate, APIKeyResponse

logger = logging.getLogger(__name__)


class APIKeyService:
    def __init__(self, apikey_repository: APIKeyRepository):
        self.apikey_repository = apikey_repository

    async def create_api_key(
        self, user_id: int, api_key_data: APIKeyCreate
    ) -> APIKeyResponse:
        """
        Creates a new API key for a user after validating uniqueness.

        Args:
            user_id: The ID of the user creating the key.
            api_key_data: The data for the new API key.

        Returns:
            The created API key details (excluding the raw key).

        Raises:
            HTTPException: 409 if key value exists, 500 on other creation errors.
        """
        existing_key = await self.apikey_repository.get_by_value(api_key_data.api_key)
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An API key with this value already exists.",
            )

        try:
            created_key: APIKey = await self.apikey_repository.create_api_key(
                user_id=user_id,
                api_key_value=api_key_data.api_key,
                service_type=api_key_data.service_type,
                domain=api_key_data.domain,
                domain_email=api_key_data.domain_email,
                project_ids=getattr(api_key_data, "project_ids", []),
                # permissions=getattr(api_key_data, 'permissions', None), # Keep example commented out
                expires_at=getattr(api_key_data, "expires_at", None),
            )
        except Exception as e:
            logger.error(
                f"Failed to create API key for user {user_id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key due to an internal error.",
            )

        return APIKeyResponse.model_validate(created_key)

    async def get_api_keys_by_user(self, user_id: int) -> List[APIKeyResponse]:
        """
        Fetches API key details for a specific user.

        Args:
            user_id: The ID of the user whose keys are to be fetched.

        Returns:
            A list of API key details (excluding the raw key). Returns empty list if none found.
        """
        api_keys: List[APIKey] = await self.apikey_repository.get_api_keys_by_user(
            user_id
        )
        return [APIKeyResponse.model_validate(key) for key in api_keys]

    async def get_api_key_by_id(self, api_key_id: int) -> APIKeyResponse:
        """
        Fetches details for a single API key by its ID.

        Args:
            api_key_id: The ID of the API key to fetch.

        Returns:
            The API key details (excluding the raw key).

        Raises:
            HTTPException: 404 if the API key is not found.
        """
        api_key = await self.apikey_repository.get_by_id(api_key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found."
            )
        return APIKeyResponse.model_validate(api_key)

    async def get_api_key_for_project(self, user_id: int, project_id: int) -> APIKey:
        """
        Fetches the API key associated with a specific user and project.

        Checks for key expiration.

        Args:
            user_id: The ID of the user.
            project_id: The ID of the project.

        Returns:
            The API key details (excluding the raw key).

        Raises:
            HTTPException: 404 if no matching key found, 403 if the key is expired.
        """
        api_key: APIKey = await self.apikey_repository.get_api_key_by_user_and_project(
            user_id, project_id
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found for this user and project combination.",
            )

        if api_key.expires_at and api_key.expires_at <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="API key has expired."
            )

        return APIKey.model_validate(api_key)

    async def delete_api_key(self, user_id: int, api_key_id: int) -> None:
        """
        Deletes an API key after verifying ownership.

        Args:
            user_id: The ID of the user requesting the deletion.
            api_key_id: The ID of the API key to delete.

        Raises:
            HTTPException: 404 if key not found, 403 if user doesn't own the key.
        """
        key_to_delete: APIKey | None = await self.apikey_repository.get_by_id(
            api_key_id
        )

        if not key_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found."
            )

        if not hasattr(key_to_delete, "user_id") or key_to_delete.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to delete this API Key.",
            )

        deleted = await self.apikey_repository.delete_api_key(api_key_id)

        if not deleted:
            logger.warning(
                f"Failed to delete API key {api_key_id} after ownership check for user {user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key could not be deleted or was already removed.",
            )
        logger.info(f"API key {api_key_id} deleted successfully by user {user_id}.")

    async def get_api_key_by_id_and_user(self, api_key_id: int, user_id: int) -> APIKey:
        """
        Fetches an API key by its ID and the user's ID.

        Args:
            api_key_id: The ID of the API key to fetch.
            user_id: The ID of the user who owns the key.

        Returns:
            The API key details (excluding the raw key).

        Raises:
            HTTPException: 404 if the key is not found, 403 if the user doesn't own the key.
        """
        api_key: APIKey = await self.apikey_repository.get_by_id_and_user(
            api_key_id, user_id
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found."
            )
        return APIKey.model_validate(api_key)
