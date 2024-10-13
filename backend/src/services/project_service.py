from repositories import ProjectRepository
from validation_models import InternalProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    async def get_all_for_user(self, user_id: int):
        return await self.project_repository.get_all_for_user(user_id)
    
    async def save_project(self, project: InternalProjectCreate, user_id: int):
        return await self.project_repository.create(user_id, project)

    async def update_project(self, user_id: int, project_id: int, project_update: ProjectUpdate):
        return await self.project_repository.update(user_id, project_id, project_update)

    async def delete_project(self, user_id: int, project_id: int):
        return await self.project_repository.delete(user_id, project_id)
