from app.repository.project_repository import ProjectRepository
from app.schema.project import ProjectCreate, ProjectUpdate, Project
from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def get_all_for_user(self, user_id: int):
        return await self.project_repository.get_all_for_user(user_id)

    async def save_project(self, project: ProjectCreate, user_id: int):
        return await self.project_repository.create(user_id, project)

    async def update_project(
        self, user_id: int, project_id: int, project_update: ProjectUpdate
    ):
        return await self.project_repository.update(user_id, project_id, project_update)

    async def get_project_by_id(self, user_id: int, project_id: int):
        project = await self.project_repository.get_by_id(user_id, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return Project.model_validate(project)

    # TOOD: check if user_id is needed or not
    async def get_project_by_external_id(self, external_project_id: int):
        return await self.project_repository.get_by_internal_id(external_project_id)

    async def delete_project_by_external_id(
        self, user_id: int, external_project_id: int
    ):
        project_id = await self.project_repository.get_project_id_by_external_id(
            external_project_id
        )
        user_projects = await self.project_repository.get_user_projects(user_id)
        if not any(project.id == project_id for project in user_projects):
            raise HTTPException(HTTP_404_NOT_FOUND, "Project does not belong to user")

        logger.info(f"Deleting project with ID: {project_id}")
        return await self.project_repository.delete(user_id, project_id)

    async def delete_embeddings_by_external_id(
        self, user_id: int, external_project_id: int
    ):
        project_id = await self.project_repository.get_project_id_by_external_id(
            external_project_id
        )
        still_associated = await self.project_repository.is_project_associated(
            project_id
        )
        return still_associated
