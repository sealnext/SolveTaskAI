from repositories import ProjectRepository
from schemas import InternalProjectCreate, ProjectUpdate
from exceptions import ProjectNotFoundError
import logging

logger = logging.getLogger(__name__)
class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    async def get_all_for_user(self, user_id: int):
        return await self.project_repository.get_all_for_user(user_id)
    
    async def save_project(self, project: InternalProjectCreate, user_id: int):
        return await self.project_repository.create(user_id, project)

    async def update_project(self, user_id: int, project_id: int, project_update: ProjectUpdate):
        return await self.project_repository.update(user_id, project_id, project_update)
    
    async def get_project_by_external_id(self, external_project_id: int):
        return await self.project_repository.get_by_internal_id(external_project_id)

    async def delete_project_by_external_id(self, user_id: int, external_project_id: int):
        project_id = await self.project_repository.get_project_id_by_external_id(external_project_id)
        user_projects = await self.project_repository.get_user_projects(user_id)
        if not any(project.id == project_id for project in user_projects):
            raise ProjectNotFoundError("Project does not belong to user")
        logger.info(f"Deleting project with ID: {project_id}")
        return await self.project_repository.delete(user_id, project_id)

    async def delete_embeddings_by_external_id(self, user_id: int, external_project_id: int):
        project_id = await self.project_repository.get_project_id_by_external_id(external_project_id)
        still_associated = await self.project_repository.is_project_associated(project_id)
        return still_associated
