from logging import getLogger
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from starlette.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_409_CONFLICT,
)

from app.dto.api_key import APIKey
from app.dto.project import Project, ProjectCreate, ProjectResponse
from app.repository.project_repository import ProjectRepository

logger = getLogger(__name__)


class ProjectService:
	def __init__(
		self,
		project_repository: ProjectRepository,
	):
		self.project_repository = project_repository

	async def get_all_for_user(self, user_id: int) -> List[Project]:
		projects_db = await self.project_repository.get_all_for_user(user_id)
		return projects_db

	async def save_project(
		self, project_data: ProjectCreate, user_id: int, api_key: APIKey
	) -> tuple[ProjectResponse, bool]:
		try:
			existing_project = await self.project_repository.get_project_by_unique_attributes(
				project_data.name, project_data.service_type, project_data.key
			)

			is_new_project = False

			if existing_project:
				already_linked = await self.project_repository.check_user_project_link(
					user_id, existing_project.id
				)
				if already_linked:
					raise HTTPException(
						HTTP_400_BAD_REQUEST, detail='User already has this project.'
					)

				final_project_db = await self.project_repository.link_user_to_existing_project(
					existing_project, user_id, api_key
				)
			else:
				final_project_db = await self.project_repository.add_project_db(
					project_data, user_id, api_key
				)
				is_new_project = True

			return ProjectResponse.model_validate(final_project_db), is_new_project

		except IntegrityError:
			raise HTTPException(HTTP_409_CONFLICT, detail='Project already exists.')

	async def get_project_by_id(self, user_id: int, project_id: int) -> Project:
		project_db = await self.project_repository.get_by_id(user_id, project_id)
		if not project_db:
			raise HTTPException(
				status.HTTP_404_NOT_FOUND,
				'Project not found',
			)

		return Project.model_validate(project_db)

	async def delete_project_by_id(self, user_id: int, internal_project_id: int) -> bool:
		is_linked = await self.project_repository.check_user_project_link(
			user_id, internal_project_id
		)
		if not is_linked:
			raise HTTPException(HTTP_404_NOT_FOUND, 'User is not associated with this project.')

		return await self.project_repository.delete(user_id, internal_project_id)

	async def is_project_still_in_use(self, external_project_id: int) -> bool:
		project_id = await self.project_repository.get_project_id_by_external_id(
			external_project_id
		)
		if not project_id:
			raise HTTPException(HTTP_404_NOT_FOUND, 'Project with specified external ID not found.')

		return await self.project_repository.is_project_associated(project_id)
