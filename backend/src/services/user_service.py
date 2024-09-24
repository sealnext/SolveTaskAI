from fastapi import Depends
from pydantic import ValidationError

from repositories import UserRepository
from exceptions import UserAlreadyExistsException, ValidationErrorException, InvalidCredentialsException
from schemas import UserCreate
from models import User
from utils.security import hash_password, verify_password

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def authenticate_user(self, username: str, password: str) -> User:
        user = await self.user_repository.get_by_username(username)
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