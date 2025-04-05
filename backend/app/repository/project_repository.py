from logging import getLogger
from typing import List

from sqlalchemy import String, and_, cast, delete, exists, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.associations import (
	api_key_project_association,
	user_project_association,
)
from app.model.project import ProjectDB
from app.model.api_key import APIKeyDB
from app.model.user import UserDB
from app.schema.project import ProjectCreate
from app.schema.api_key import APIKey
from app.service.ticketing.enums import TicketingSystemType

logger = getLogger(__name__)


class ProjectRepository:
	def __init__(self, db_session: AsyncSession):
		self.db_session = db_session

	async def get_by_external_id(self, external_project_id: int) -> ProjectDB | None:
		stmt = select(ProjectDB).where(ProjectDB.external_id == str(external_project_id))
		result = await self.db_session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_project_by_unique_attributes(
		self, name: str, service_type: TicketingSystemType, key: str
	) -> ProjectDB | None:
		stmt = select(ProjectDB).where(
			and_(
				ProjectDB.name == name,
				ProjectDB.service_type == service_type,
				ProjectDB.key == key,
			)
		)
		result = await self.db_session.execute(stmt)
		return result.scalar_one_or_none()

	async def check_user_project_link(self, user_id: int, project_id: int) -> bool:
		stmt = select(
			exists().where(
				and_(
					user_project_association.c.user_id == user_id,
					user_project_association.c.project_id == project_id,
				)
			)
		)
		result = await self.db_session.execute(stmt)
		return result.scalar()

	async def check_other_user_project_link(self, user_id: int, project_id: int) -> bool:
		stmt = select(func.count(user_project_association.c.user_id)).where(
			and_(
				user_project_association.c.project_id == project_id,
				user_project_association.c.user_id != user_id,
			)
		)
		result = await self.db_session.execute(stmt)
		count = result.scalar()
		return count > 0

	async def link_user_to_existing_project(
		self, existing_project: ProjectDB, user_id: int, api_key: APIKey
	) -> ProjectDB:
		await self._link_entities_to_project(existing_project, user_id, api_key)
		await self.db_session.flush()

		await self.db_session.refresh(existing_project)
		return existing_project

	async def add_project_db(
		self, project_data: ProjectCreate, user_id: int, api_key: APIKey
	) -> ProjectDB:
		db_project = ProjectDB()
		db_project.domain = project_data.domain
		db_project.external_id = project_data.external_id
		db_project.name = project_data.name
		db_project.key = project_data.key
		db_project.service_type = project_data.service_type

		self.db_session.add(db_project)

		await self._link_entities_to_project(db_project, user_id, api_key)

		await self.db_session.flush()

		return db_project

	async def _link_entities_to_project(
		self, project_db: ProjectDB, user_id: int, api_key: APIKey = None
	) -> None:
		user_db = await self.db_session.get(UserDB, user_id)
		project_db.users.append(user_db)

		api_key_db = await self.db_session.get(APIKeyDB, api_key.id)
		project_db.api_keys.append(api_key_db)

	async def get_project_by_id_with_relations(self, project_id: int) -> ProjectDB | None:
		stmt = (
			select(ProjectDB)
			.options(selectinload(ProjectDB.users), selectinload(ProjectDB.api_keys))
			.where(ProjectDB.id == project_id)
		)
		result = await self.db_session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_by_id(self, user_id: int, project_id: int) -> ProjectDB | None:
		query = (
			select(ProjectDB)
			.join(user_project_association)
			.where(
				and_(
					ProjectDB.id == project_id,
					user_project_association.c.user_id == user_id,
				)
			)
		)
		result = await self.db_session.execute(query)
		return result.scalar_one_or_none()

	async def get_all_for_user(self, user_id: int) -> List[ProjectDB]:
		query = (
			select(ProjectDB)
			.join(user_project_association)
			.where(user_project_association.c.user_id == user_id)
		)
		result = await self.db_session.execute(query)
		return result.scalars().all()

	async def delete(self, user_id: int, project_id: int) -> bool:
		"""
		Deletes the link between a user and a project.
		If this is the last user linked to the project, deletes the project
		and associated shared resources (APIKey links).
		Returns True if the project itself was deleted, False otherwise.
		Relies on an outer transaction managed by get_db_session.
		"""
		project_was_deleted = False
		is_linked = await self.check_user_project_link(user_id, project_id)
		if not is_linked:
			logger.warning(
				f'User {user_id} attempted to delete project {project_id} they are not linked to.'
			)
			return False

		await self.db_session.execute(
			delete(user_project_association).where(
				and_(
					user_project_association.c.project_id == project_id,
					user_project_association.c.user_id == user_id,
				)
			)
		)
		await self.db_session.flush()

		other_users_exist = await self.check_other_user_project_link(user_id, project_id)

		if not other_users_exist:
			logger.info(
				f'No other users linked to project {project_id}. Deleting shared resources.'
			)
			await self.db_session.execute(
				delete(api_key_project_association).where(
					api_key_project_association.c.project_id == project_id
				)
			)
			delete_project_stmt = delete(ProjectDB).where(ProjectDB.id == project_id)
			result = await self.db_session.execute(delete_project_stmt)

			if result.rowcount > 0:
				project_was_deleted = True
				logger.info(f'Project {project_id} deleted successfully.')
			else:
				logger.warning(
					f'Project {project_id} was expected to be deleted, but delete operation reported 0 rows affected.'
				)

		else:
			logger.info(
				f'Other users still linked to project {project_id}. Only removing link for user {user_id}.'
			)
			project_was_deleted = False

		return project_was_deleted

	async def get_with_related(self, user_id: int, project_id: int) -> ProjectDB | None:
		query = (
			select(ProjectDB)
			.options(
				selectinload(ProjectDB.api_keys),
				selectinload(ProjectDB.embeddings),
				selectinload(ProjectDB.users),
			)
			.join(user_project_association)
			.where(
				and_(
					ProjectDB.id == project_id,
					user_project_association.c.user_id == user_id,
				)
			)
		)
		result = await self.db_session.execute(query)
		return result.scalar_one_or_none()

	async def get_by_domain(self, user_id: int, domain: str) -> ProjectDB | None:
		query = (
			select(ProjectDB)
			.join(user_project_association)
			.where(
				and_(
					ProjectDB.domain == domain,
					user_project_association.c.user_id == user_id,
				)
			)
		)
		result = await self.db_session.execute(query)
		return result.scalar_one_or_none()

	async def get_project_id_by_external_id(self, external_project_id: int) -> int | None:
		query = select(ProjectDB.id).where(
			ProjectDB.external_id == cast(str(external_project_id), String)
		)
		result = await self.db_session.execute(query)
		return result.scalar_one_or_none()

	async def is_project_associated(self, project_id: int) -> bool:
		query = select(exists().where(user_project_association.c.project_id == project_id))
		result = await self.db_session.execute(query)
		return result.scalar()
