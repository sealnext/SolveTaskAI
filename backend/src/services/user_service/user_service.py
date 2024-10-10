from datetime import datetime, UTC
import logging
from pydantic import ValidationError
from fastapi import Depends, Request
from fastapi_csrf_protect import CsrfProtect
from typing import Optional, Tuple

from repositories import UserRepository
from exceptions import (
    UserAlreadyExistsException,
    ValidationErrorException,
    InvalidCredentialsException,
    InvalidTokenException,
    UserNotFoundException,
    SecurityException,
    UnexpectedErrorException,
    APIKeyNotFoundException,
    APIKeyExpiredException
)
from validation_models import UserCreate
from models import User
from utils.security import hash_password, verify_password
from services import AuthService
from utils.security import decode_next_auth_token

from repositories.apikey_repository import get_api_key_by_user_and_project

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_current_user(self, request: Request) -> User:
        next_auth_token = request.cookies.get("next-auth.session-token")
        if not next_auth_token:
            logger.info("Next-auth token is missing from the request cookies")
            raise InvalidTokenException("Next-auth token is missing")

        try:
            session_data = decode_next_auth_token(next_auth_token)
            token = session_data.get("access_token")
            if not token:
                logger.info("Access token is missing in the session data")
                raise InvalidTokenException("Access token is missing")

            device_info, location = AuthService.extract_request_localization(request)
            email = AuthService.verify_and_decode_token(token, device_info, location)

            user = await self.user_repository.get_by_email(email)
            if user is None:
                logger.info(f"User with email {email} not found")
                raise UserNotFoundException("User not found")

            return user

        except (InvalidTokenException, UserNotFoundException, SecurityException) as e:
            logger.error(f"Authorization failed: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during authorization: {str(e)}")
            raise UnexpectedErrorException("An unexpected error occurred during authorization")

    async def create_new_user(self, user_create: UserCreate) -> User:
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

    async def get_user_by_email(self, email: str) -> Optional[User]:
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