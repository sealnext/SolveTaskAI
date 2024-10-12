from repositories import ProjectRepository

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    async def get_all_for_user(self, user_id: int):
        return await self.project_repository.get_all_for_user(user_id)
    