from repositories import ProjectRepository
from validation_models import InternalProjectCreate, ProjectUpdate
from exceptions import ProjectNotFoundError

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    async def get_all_for_user(self, user_id: int):
        return await self.project_repository.get_all_for_user(user_id)
    
    async def save_project(self, project: InternalProjectCreate, user_id: int):
        return await self.project_repository.create(user_id, project)

    async def update_project(self, user_id: int, project_id: int, project_update: ProjectUpdate):
        return await self.project_repository.update(user_id, project_id, project_update)

    async def delete_project_by_external_id(self, user_id: int, external_project_id: int):
        project_id = await self.project_repository.get_project_id_by_external_id(external_project_id)
        user_projects = await self.project_repository.get_user_projects(user_id)
        print("--- delete_project_by_external_id ---")
        print(project_id)
        print(user_projects)
        if not any(project.id == project_id for project in user_projects):
            raise ProjectNotFoundError("Project does not belong to user")
        print("--- deleting project ---")
        return await self.project_repository.delete(user_id, project_id)