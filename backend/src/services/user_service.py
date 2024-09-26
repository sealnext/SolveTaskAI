from fastapi import Depends
from pydantic import ValidationError
import logging

from repositories import UserRepository
from exceptions import UserAlreadyExistsException, ValidationErrorException, InvalidCredentialsException
from schemas import UserCreate
from models import User
from utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsException("User not found")
        try:
            if not verify_password(password, user.hashed_password):
                raise InvalidCredentialsException("Invalid password")
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            raise InvalidCredentialsException("An error occurred during authentication")
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