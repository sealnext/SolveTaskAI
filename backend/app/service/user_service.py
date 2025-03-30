from datetime import datetime, UTC
import logging
from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
)
from pydantic import ValidationError
from typing import Optional, List

from app.repository.user_repository import UserRepository
from app.repository.apikey_repository import APIKeyRepository
from app.schema.user import UserCreate
from app.schema.api_key import APIKey
from app.model.user import UserDB


logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self, user_repository: UserRepository, api_key_repository: APIKeyRepository
    ):
        self.user_repository = user_repository
        self.api_key_repository = api_key_repository

    async def get_api_keys_by_user(self, user: UserDB) -> List[APIKey]:
        api_keys = await self.api_key_repository.get_api_keys_by_user(user.id)
        # decrypt api keys, for the moment we dont store them encrypted
        # TODO: encrypt them

        # TODO: add caching

        # show only the first 5 characters of the api key
        for api_key in api_keys:
            api_key.api_key = api_key.api_key[:5] + "*****"

        if not api_keys:
            raise HTTPException(HTTP_200_OK, "No API keys found")

        return api_keys

    async def get_api_key_by_id(self, api_key_id: int, user_id: int) -> APIKey:
        api_key = await self.api_key_repository.get_by_id(api_key_id, user_id)
        return api_key

    async def create_new_user(self, user_create: UserCreate) -> UserDB:
        existing_user = await self.user_repository.get_by_email(user_create.email)
        if existing_user:
            logger.info(
                f"User creation failed: User with email {user_create.email} already exists"
            )
            raise HTTPException(HTTP_400_BAD_REQUEST, "User already exists")

        hashed_password = user_create.password
        user_create.password = hashed_password

        try:
            return await self.user_repository.create(user_create)

        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e.errors()}")
            raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, "Validation error")

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        return await self.user_repository.get_by_email(email)

    async def get_api_key_for_project(self, project_id: int) -> str:
        api_key = await self.user_repository.get_api_key_for_project(
            self.user.id, project_id
        )
        if not api_key:
            raise HTTPException(HTTP_200_OK, "API key not found")

        if api_key.expires_at and api_key.expires_at <= datetime.now(UTC):
            raise HTTPException(HTTP_403_FORBIDDEN, "API key expired")

        return api_key.key
