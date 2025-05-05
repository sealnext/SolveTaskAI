from typing import List

from sqlalchemy import String, and_, cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dto.api_key import ApiKey
from app.dto.project import ProjectCreate
from app.model.api_key import ApiKeyDB
from app.model.associations import user_project_association
from app.model.project import ProjectDB
from app.model.user import UserDB
from app.service.ticketing.enums import TicketingSystemType


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
		return bool(result.scalar())

	async def check_other_user_project_link(self, user_id: int, project_id: int) -> bool:
		stmt = select(func.count(user_project_association.c.user_id)).where(
			and_(
				user_project_association.c.project_id == project_id,
				user_project_association.c.user_id != user_id,
			)
		)
		result = await self.db_session.execute(stmt)
		count = result.scalar()
		return (count or 0) > 0

	async def link_user_to_existing_project(
		self, existing_project: ProjectDB, user_id: int, api_key: ApiKey
	) -> ProjectDB | None:
		"""
		Link an existing project to a user and an his API key.
		"""
		stmt = (
			select(ProjectDB)
			.options(selectinload(ProjectDB.users), selectinload(ProjectDB.api_keys))
			.where(ProjectDB.id == existing_project.id)
		)
		result = await self.db_session.execute(stmt)
		project = result.scalar_one_or_none()

		if not project:
			return None

		user_already_linked = False
		for user in project.users:
			if user.id == user_id:
				user_already_linked = True
				break

		if user_already_linked:
			return project

		user_db = await self.db_session.get(UserDB, user_id)
		if user_db:
			project.users.append(user_db)

		if api_key:
			api_key_db = await self.db_session.get(ApiKeyDB, api_key.id)
			if api_key_db:
				project.api_keys.append(api_key_db)

		await self.db_session.flush()

		return project

	async def add_project_db(
		self, project_data: ProjectCreate, user_id: int, api_key: ApiKey
	) -> ProjectDB:
		db_project = ProjectDB(
			name=project_data.name,
			domain=project_data.domain,
			service_type=project_data.service_type,
			key=project_data.key,
			external_id=project_data.external_id,
		)

		self.db_session.add(db_project)

		user_db = await self.db_session.get(UserDB, user_id)
		if user_db:
			db_project.users.append(user_db)

		if api_key:
			api_key_db = await self.db_session.get(ApiKeyDB, api_key.id)
			if api_key_db:
				db_project.api_keys.append(api_key_db)

		await self.db_session.flush()

		return db_project

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
		return list(result.scalars().all())

	async def delete(self, user_id: int, project_id: int) -> bool:
		"""
		Deletes the link between a user and a project.
		If this is the last user linked to the project, deletes the project and all associated resources.
		If other users remain, removes the user's API keys from the project if they aren't used by other users.
		Returns True if the project itself was deleted, False otherwise.
		"""
		# Get project directly using get() instead of select for PK lookup
		project = await self.db_session.get(
			ProjectDB,
			project_id,
			options=[selectinload(ProjectDB.users), selectinload(ProjectDB.api_keys)],
		)

		if not project:
			return False

		# Find the user to unlink - use get() for PK lookup
		user_to_remove = await self.db_session.get(UserDB, user_id)
		if not user_to_remove or user_to_remove not in project.users:
			return False

		# Remove the user from the project
		project.users.remove(user_to_remove)

		# Find and remove user's API keys from project
		project.api_keys = [api_key for api_key in project.api_keys if api_key.user_id != user_id]

		# If no users left, delete the project
		if not project.users:
			await self.db_session.delete(project)

		await self.db_session.flush()
		return not bool(project.users)

	async def get_with_related(self, user_id: int, project_id: int) -> ProjectDB | None:
		query = (
			select(ProjectDB)
			.options(
				selectinload(ProjectDB.api_keys),
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
		return bool(result.scalar())
