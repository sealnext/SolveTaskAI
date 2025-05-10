from app.dto.user import Email, UserCreateByPassword, UserPublic
from app.misc.crypto import password_hasher
from app.misc.exception import UserNotFoundException
from app.misc.logger import logger
from app.model.user import UserDB
from app.repository.user import UserRepository


class UserService:
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository

	async def create_user_by_password(self, user_dto: UserCreateByPassword) -> UserDB:
		hashed_password = password_hasher.hash(user_dto.password)
		user = await self.user_repository.create_by_password(
			email=str(user_dto.email), hashed_password=hashed_password
		)
		return user

	async def get_user_by_email(self, email_dto: Email) -> UserDB:
		user: UserDB | None = await self.user_repository.get_user_by_email(str(email_dto.email))
		if user is None:
			raise UserNotFoundException('User not found by email')
		return user

	async def get_user_profile(self, user_id: int) -> UserPublic:
		user: UserDB | None = await self.user_repository.get_user_by_id(user_id)
		if user is None:
			raise UserNotFoundException('User not found by id')
		return UserPublic(
			name=user.name,
			email=user.email,
			is_email_verified=user.is_email_verified,
		)

	async def email_exists(self, email: str) -> bool:
		user: UserDB | None = await self.user_repository.get_user_by_email(email)
		return user is not None

	async def verify_email(self, user_id: int) -> None:
		user = await self.user_repository.update_user(user_id, is_email_verified=True)
		logger.info('User (id: %s) verified their email', user.id)
