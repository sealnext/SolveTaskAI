from datetime import datetime, UTC
import logging
from pydantic import ValidationError
from fastapi import Depends, Request
from typing import Optional, Tuple, List

from repositories import UserRepository, APIKeyRepository
from exceptions import (
    UserAlreadyExistsException,
    ValidationErrorException,
    InvalidCredentialsException,
    APIKeyNotFoundException,
    APIKeyExpiredException
)
from schemas import UserCreate, APIKey
from models import UserDB
from utils.security import hash_password, verify_password
from services import AuthService


logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository, api_key_repository: APIKeyRepository):
        self.user_repository = user_repository
        self.api_key_repository = api_key_repository

    async def get_api_keys_by_user(self, user: UserDB) -> List[APIKey]:
        api_keys = await self.api_key_repository.get_api_keys_by_user(user.id)
        # decrypt api keys, for the moment we dont store them encrypted
        # TODO: encrypt them

        # TODO: add caching

        # show only the first 5 characters of the api key
        for api_key in api_keys:
            api_key.api_key = api_key.api_key[:5] + '*****'

        if not api_keys:
            raise APIKeyNotFoundException
        return api_keys

    async def get_api_key_by_id(self, api_key_id: int, user_id: int) -> APIKey:
        api_key = await self.api_key_repository.get_by_id(api_key_id, user_id)
        return api_key

    async def create_new_user(self, user_create: UserCreate) -> UserDB:
        existing_user = await self.user_repository.get_by_email(user_create.email)
        if existing_user:
            logger.info(f"User creation failed: User with email {user_create.email} already exists")
            raise UserAlreadyExistsException(f"User already exists")

        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password

        try:
            return await self.user_repository.create(user_create)

        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e.errors()}")
            raise ValidationErrorException(f"Validation error: {e.errors()}")

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        return await self.user_repository.get_by_email(email)

    async def authenticate_and_get_tokens(self, email: str, password: str, request: Request, auth_service: AuthService) -> Tuple[str, str]:
        try:
            user = await self.authenticate_user(email, password)
            return auth_service.create_token_pair(user.email, request)
        except InvalidCredentialsException as e:
            logger.warning(f"Authentication failed for email {email}: {str(e)}")
            raise

    async def get_api_key_for_project(self, project_id: int) -> str:
        api_key = await self.user_repository.get_api_key_for_project(self.user.id, project_id)
        if not api_key:
            raise APIKeyNotFoundException

        if api_key.expires_at and api_key.expires_at <= datetime.now(UTC):
            raise APIKeyExpiredException

        return api_key.key