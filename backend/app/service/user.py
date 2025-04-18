from fastapi import HTTPException, status

from app.dto.user import Email, UserCreateByPassword
from app.misc.exception import UserAlreadyExistsException
from app.misc.security import password_hasher
from app.model.user import UserDB
from app.repository.user import UserRepository


class UserService:
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository

	async def create_user_by_password(self, user_dto: UserCreateByPassword) -> UserDB:
		is_email_already = await self.user_repository.check_user_exists_by_email(
			str(user_dto.email)
		)
		if is_email_already:
			raise UserAlreadyExistsException('Email is already registered')
		hashed_password = password_hasher.hash(user_dto.password)
		user = await self.user_repository.create_by_password(
			email=str(user_dto.email), name=user_dto.name, hashed_password=hashed_password
		)
		return user

	async def get_user_by_email(self, email_dto: Email) -> UserDB:
		user: UserDB | None = await self.user_repository.get_user_by_email(str(email_dto.email))
		if not user:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'User not found')
		return user
