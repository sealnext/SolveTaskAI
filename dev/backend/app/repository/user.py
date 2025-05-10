from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.misc.exception import UserNotFoundException
from app.model.user import UserDB


class UserRepository:
	def __init__(self, async_db_session: AsyncSession):
		self.async_db_session = async_db_session

	async def create_by_password(self, email: str, hashed_password: str) -> UserDB:
		user = UserDB(email=email, hashed_password=hashed_password)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def create_by_github(self, name: str, email: str, github_id: str) -> UserDB:
		user = UserDB(name=name, email=email, is_email_verified=True, google_id=github_id)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def create_by_google(self, name: str, email: str, google_id: str) -> UserDB:
		user = UserDB(name=name, email=email, is_email_verified=True, google_id=google_id)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def get_user_by_email(self, email: str) -> UserDB | None:
		result = await self.async_db_session.execute(select(UserDB).where(UserDB.email == email))
		return result.scalar()

	async def does_email_exist(self, email: str) -> bool:
		result = await self.async_db_session.execute(select(UserDB).where(UserDB.email == email))
		return result.scalar() is not None

	async def get_user_by_id(self, user_id: int) -> UserDB | None:
		result = await self.async_db_session.execute(select(UserDB).where(UserDB.id == user_id))
		return result.scalar()

	async def update_user(self, user_id: int, **kwargs) -> UserDB:
		user = await self.async_db_session.get(UserDB, user_id)
		if user is None:
			raise UserNotFoundException('User not found by id')

		for key, value in kwargs.items():
			if hasattr(user, key):
				setattr(user, key, value)

		await self.async_db_session.flush()
		return user
