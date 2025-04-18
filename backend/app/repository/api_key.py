from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.api_key import ApiKey
from app.model.api_key import ApiKeyDB
from app.model.associations import api_key_project_association
from app.model.project import ProjectDB
from app.service.ticketing.enums import TicketingSystemType


class ApiKeyRepository:
	def __init__(self, db_session: AsyncSession):
		self.db_session = db_session

	async def get_by_id(self, api_key_id: int) -> ApiKey | None:
		stmt = select(ApiKeyDB).where(ApiKeyDB.id == api_key_id)
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)

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

	async def get_api_keys_by_user(self, user_id: int) -> List[ApiKey]:
		stmt = select(ApiKeyDB).where(ApiKeyDB.user_id == user_id)
		result = await self.db_session.execute(stmt)
		db_keys = result.scalars().all()
		return [ApiKey.model_validate(key) for key in db_keys]

	async def get_api_key_by_user_and_project(self, user_id: int, project_id: int) -> ApiKey | None:
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
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)

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

	async def create_api_key(
		self,
		user_id: int,
		api_key_value: str,
		service_type: TicketingSystemType,
		domain: str,
		domain_email: str,
		project_ids: List[int],
		expires_at: datetime | None = None,
	) -> ApiKey:
		project_stmt = select(ProjectDB).where(ProjectDB.id.in_(project_ids))
		project_result = await self.db_session.execute(project_stmt)
		projects = project_result.scalars().all()
		if len(projects) != len(project_ids):
			found_ids = {p.id for p in projects}
			missing_ids = set(project_ids) - found_ids
			# TODO: Consider logging a warning or raising an error
			print(f'Warning: Projects not found for IDs: {missing_ids}')

		db_key = ApiKeyDB(
			user_id=user_id,
			api_key=api_key_value,
			service_type=service_type,
			domain=domain,
			domain_email=domain_email,
			expires_at=expires_at,
			projects=projects,
		)

		self.db_session.add(db_key)
		await self.db_session.flush()
		await self.db_session.refresh(db_key, attribute_names=['id', 'created_at'])
		await self.db_session.refresh(db_key, attribute_names=['projects'])

		return ApiKey.model_validate(db_key)

	async def delete_api_key(self, api_key_id: int) -> bool:
		stmt_select = select(ApiKeyDB).where(ApiKeyDB.id == api_key_id)
		result = await self.db_session.execute(stmt_select)
		db_key = result.scalar_one_or_none()

		if db_key:
			await self.db_session.delete(db_key)
			return True
		return False

	async def get_by_id_and_user(self, api_key_id: int, user_id: int) -> ApiKey | None:
		stmt = select(ApiKeyDB).where((ApiKeyDB.id == api_key_id) & (ApiKeyDB.user_id == user_id))
		result = await self.db_session.execute(stmt)
		db_key = result.scalar_one_or_none()
		if db_key is None:
			return None
		return ApiKey.model_validate(db_key)
