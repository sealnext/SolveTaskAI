from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import UserDB


class UserRepository:
	def __init__(self, async_db_session: AsyncSession):
		self.async_db_session = async_db_session

	async def create_by_password(self, name: str, email: str, hashed_password: str) -> UserDB:
		user = UserDB(name=name, email=email, hashed_password=hashed_password)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def create_by_github(self, name: str, email: str, github_id: str) -> UserDB:
		user = UserDB(name=name, email=email, google_id=github_id)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def create_by_google(self, name: str, email: str, google_id: str) -> UserDB:
		user = UserDB(name=name, email=email, google_id=google_id)
		self.async_db_session.add(user)
		await self.async_db_session.flush()
		return user

	async def check_user_exists_by_email(self, email: str) -> bool:
		result = await self.async_db_session.execute(select(exists().where(UserDB.email == email)))
		return result.scalar() is True

	async def get_user_by_email(self, email: str) -> UserDB | None:
		result = await self.async_db_session.execute(select(UserDB).where(UserDB.email == email))
		return result.scalar()
