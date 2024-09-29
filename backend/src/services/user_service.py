import logging
from pydantic import ValidationError
from fastapi import Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from typing import Optional

from repositories import UserRepository
from exceptions import UserAlreadyExistsException, ValidationErrorException, InvalidCredentialsException, InvalidTokenException, UserNotFoundException
from validation_models import UserCreate
from models import User
from utils.security import hash_password, verify_password
from services import AuthService
from utils.security import decode_next_auth_token

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @staticmethod
    async def get_current_user(
        request: Request,
        csrf_protect: CsrfProtect = Depends(),
    ) -> User:
        try:
            next_auth_token = request.cookies.get("next-auth.session-token")
            if not next_auth_token:
                raise InvalidTokenException("Next-auth token is missing")

            session_data = decode_next_auth_token(next_auth_token)
            csrf_protect.validate_csrf(session_data.get("csrf_token"))
            token = session_data.get("access_token")
            if not token:
                raise InvalidTokenException("Access token is missing")

            device_info, location = AuthService.extract_request_localization(request)

            email = AuthService.verify_and_decode_token(token, device_info, location)
            user = await UserService.get_user_by_email(email)
            if user is None:
                raise UserNotFoundException
            return user
        except Exception as e:
            logger.error(f"Authorization failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed authorization")


    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException
        return user

    async def create_new_user(self, user_create: UserCreate) -> User:
        try:
            existing_user = await self.user_repository.get_by_email(user_create.email)
            if existing_user:
                raise UserAlreadyExistsException

            hashed_password = hash_password(user_create.password)
            user_create.password = hashed_password
            return await self.user_repository.create(user_create)
        except ValidationError as e:
            raise ValidationErrorException(f"Validation error: {e.errors()}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_repository.get_by_email(email)