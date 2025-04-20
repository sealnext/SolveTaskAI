from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.api_key import ApiKey, ApiKeyCreate
from app.model.api_key import ApiKeyDB
from app.model.associations import api_key_project_association
from app.service.ticketing.enums import TicketingSystemType
from app.model.user import UserDB


class ApiKeyRepository:
	def __init__(self, db_session: AsyncSession):
		self.db_session = db_session

	async def get_by_id(self, api_key_id: int) -> ApiKeyDB | None:
		stmt = select(ApiKeyDB).where(ApiKeyDB.id == api_key_id)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		return db_key

	async def get_by_value(self, api_key_value: str) -> ApiKey | None:
		stmt = select(ApiKeyDB).where(ApiKeyDB.api_key == api_key_value)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)

	async def get_by_project_id_and_user(self, project_id: int, user_id: int) -> ApiKey | None:
		stmt = (
			select(ApiKeyDB)
			.join(api_key_project_association)
			.where(
				(api_key_project_association.c.project_id == project_id)
				& (ApiKeyDB.user_id == user_id)
			)
		)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)

	async def get_api_keys_by_user(self, user_id: int) -> List[ApiKeyDB]:
		stmt = select(ApiKeyDB).where(ApiKeyDB.user_id == user_id)
		result = await self.db_session.execute(stmt)
		db_keys = result.scalars().all()
		return list(db_keys)

	async def get_api_key_by_project(self, user_id: int, project_id: int) -> ApiKeyDB | None:
		stmt = (
			select(ApiKeyDB)
			.join(api_key_project_association)
			.where(
				(ApiKeyDB.user_id == user_id)
				& (api_key_project_association.c.project_id == project_id)
			)
		)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		return db_key

	async def get_api_key_by_user_and_service(
		self, user_id: int, service_type: TicketingSystemType
	) -> ApiKey | None:
		stmt = select(ApiKeyDB).where(
			(ApiKeyDB.user_id == user_id) & (ApiKeyDB.service_type == service_type)
		)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)

	async def create_api_key(self, user_id: int, api_key_data: ApiKeyCreate) -> ApiKeyDB:
		"""Creates a new API key for a user.

		Args:
			user_id: The ID of the user creating the key
			api_key_data: The API key creation data containing service type, key value, domain, etc.

		Returns:
			The created API key
		"""
		db_key = ApiKeyDB(
			user_id=user_id,
			api_key=api_key_data.api_key,
			service_type=api_key_data.service_type,
			domain=api_key_data.domain,
			domain_email=str(api_key_data.domain_email),
		)

		self.db_session.add(db_key)
		await self.db_session.flush()
		await self.db_session.refresh(db_key)

		return db_key

	async def delete_api_key(self, api_key_id: int) -> bool:
		api_key = await self.db_session.get(ApiKeyDB, api_key_id)
		if not api_key:
			return False

		await self.db_session.delete(api_key)
		await self.db_session.flush()
		return True

	async def get_by_id_and_user(self, api_key_id: int, user_id: int) -> ApiKey | None:
		stmt = select(ApiKeyDB).where((ApiKeyDB.id == api_key_id) & (ApiKeyDB.user_id == user_id))
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)
