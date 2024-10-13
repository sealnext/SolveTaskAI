from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, text
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from models import Project, User, user_project_association
from validation_models import ProjectUpdate, InternalProjectCreate

async def get_project_repository(db_session: AsyncSession):
    return ProjectRepository(db_session)

class ProjectRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, user_id: int, project: InternalProjectCreate) -> Project:
        try:
            db_project = Project(**project.model_dump())
            self.db_session.add(db_project)
            await self.db_session.flush()

            stmt = select(User).where(User.id == user_id).options(selectinload(User.projects))
            result = await self.db_session.execute(stmt)
            user = result.scalar_one()

            user.projects.append(db_project)
            await self.db_session.commit()
            await self.db_session.refresh(db_project)
            return db_project
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                await self.db_session.execute(text("SELECT setval('projects_id_seq', (SELECT MAX(id) FROM projects))"))
                await self.db_session.rollback()
                return await self.create(user_id, project)
            raise

    async def get_by_id(self, user_id: int, project_id: int) -> Optional[Project]:
        query = (
            select(Project)
            .join(user_project_association)
            .where(and_(Project.id == project_id, user_project_association.c.user_id == user_id))
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: int) -> List[Project]:
        query = (
            select(Project)
            .join(user_project_association)
            .where(user_project_association.c.user_id == user_id)
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def update(self, user_id: int, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
        project = await self.get_by_id(user_id, project_id)
        if project:
            for key, value in project_update.model_dump(exclude_unset=True).items():
                setattr(project, key, value)
            await self.db_session.flush()
            await self.db_session.refresh(project)
        return project

    async def delete(self, user_id: int, project_id: int) -> bool:
        project = await self.get_by_id(user_id, project_id)
        if project:
            await self.db_session.delete(project)
            await self.db_session.flush()
            return True
        return False

    async def get_with_related(self, user_id: int, project_id: int) -> Optional[Project]:
        query = (
            select(Project)
            .options(
                selectinload(Project.api_keys),
                selectinload(Project.embeddings),
                selectinload(Project.users)
            )
            .join(user_project_association)
            .where(and_(Project.id == project_id, user_project_association.c.user_id == user_id))
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_domain(self, user_id: int, domain: str) -> Optional[Project]:
        query = (
            select(Project)
            .join(user_project_association)
            .where(and_(Project.domain == domain, user_project_association.c.user_id == user_id))
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def add_user_to_project(self, project_id: int, user_id: int) -> bool:
        project = await self.db_session.get(Project, project_id)
        user = await self.db_session.get(User, user_id)
        if project and user:
            project.users.append(user)
            await self.db_session.commit()
            return True
        return False

    async def remove_user_from_project(self, project_id: int, user_id: int) -> bool:
        project = await self.db_session.get(Project, project_id)
        user = await self.db_session.get(User, user_id)
        if project and user and user in project.users:
            project.users.remove(user)
            await self.db_session.commit()
            return True
        return False
