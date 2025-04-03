from logging import getLogger

from fastapi import HTTPException, status
from pydantic import ValidationError

# Removed APIKey import as it's no longer used here
from app.model.user import UserDB
from app.repository.user_repository import UserRepository

# Removed APIKeyRepository import as it's no longer used here
from app.schema.user import UserCreate, UserRead

logger = getLogger(__name__)


class UserService:
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository

	async def create_new_user(self, user_create: UserCreate) -> UserDB:
		existing_user = await self.user_repository.get_by_email(user_create.email)
		if existing_user:
			logger.info(f'User creation failed: User with email {user_create.email} already exists')
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'User already exists')

		hashed_password = user_create.password
		user_create.password = hashed_password

		try:
			return await self.user_repository.create(user_create)

		except ValidationError as e:
			logger.error(f'Validation error during user creation: {e.errors()}')
			raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, 'Validation error')

	async def get_user_by_email(self, email: str) -> UserRead | None:
		user: UserDB | None = await self.user_repository.get_by_email(email)
		if not user:
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'User not found')
		return UserRead.model_validate(user)
