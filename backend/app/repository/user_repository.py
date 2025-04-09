from argon2 import PasswordHasher
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.user import UserCreateEmail
from app.model.user import UserDB


class UserRepository:
	def __init__(self, async_db_session: AsyncSession):
		self.async_db_session = async_db_session

	def create_by_email(self, user_dto: UserCreateEmail) -> None:
		hasher = PasswordHasher()
		hashed_password = hasher.hash(user_dto.password)
		user = UserDB(name=user_dto.name, email=user_dto.email, hashed_password=hashed_password)
		self.async_db_session.add(user)

	async def get_by_email(self, email: str) -> UserDB | None:
		query = select(UserDB).where(UserDB.email == email)
		result = await self.async_db_session.execute(query)
		return result.scalar_one_or_none()

	async def get_by_id(self, user_id: int) -> UserDB | None:
		query = select(UserDB).where(UserDB.id == user_id)
		result = await self.async_db_session.execute(query)
		return result.scalar_one_or_none()

	async def update_password(self, user_id: int, new_password: str) -> None:
		query = update(UserDB).where(UserDB.id == user_id).values(hashed_password=new_password)
		await self.async_db_session.execute(query)
		await self.async_db_session.commit()
