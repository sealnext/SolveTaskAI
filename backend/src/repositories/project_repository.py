from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, text, cast, String, insert
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from models import Project, User, APIKey, user_project_association, api_key_project_association
from schemas import ProjectUpdate, InternalProjectCreate
from exceptions import ProjectAlreadyExistsError

async def get_project_repository(db_session: AsyncSession):
    return ProjectRepository(db_session)

class ProjectRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create(self, user_id: int, project: InternalProjectCreate) -> Project:
        try:
            # Check if project already exists
            existing_project = await self.get_by_internal_id(project.internal_id)
            if existing_project:
                raise ProjectAlreadyExistsError(f"Contextual project already exist for this project")

            api_key_id = project.api_key_id
            project_data = project.model_dump(exclude={'api_key_id'})
            
            db_project = Project(**project_data)
            self.db_session.add(db_project)
            await self.db_session.flush()

            # Add user-project association
            await self.db_session.execute(
                insert(user_project_association).values(
                    user_id=user_id, project_id=db_project.id
                )
            )

            # Add api-key-project association
            await self.db_session.execute(
                insert(api_key_project_association).values(
                    api_key_id=api_key_id, project_id=db_project.id
                )
            )

            await self.db_session.flush()
            
            # Reload the project with all its relations
            stmt = select(Project).options(
                selectinload(Project.api_keys),
                selectinload(Project.users)
            ).where(Project.id == db_project.id)
            result = await self.db_session.execute(stmt)
            db_project = result.scalar_one()

            await self.db_session.commit()

            return db_project
        except IntegrityError as e:
            await self.db_session.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                raise ProjectAlreadyExistsError(f"Project with these details already exists: {str(e)}")
            raise

    async def create_with_retry(self, user_id: int, project: InternalProjectCreate) -> Project:
        try:
            return await self.create(user_id, project)
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                await self.db_session.rollback()
                return await self.create_with_retry(user_id, project)
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
            # Remove the user-project association
            user_project_delete_stmt = delete(user_project_association).where(
                (user_project_association.c.user_id == user_id) &
                (user_project_association.c.project_id == project_id)
            )
            await self.db_session.execute(user_project_delete_stmt)

            # Remove the api-key-project associations
            api_key_project_delete_stmt = delete(api_key_project_association).where(
                api_key_project_association.c.project_id == project_id
            )
            await self.db_session.execute(api_key_project_delete_stmt)

            # Delete the project
            await self.db_session.delete(project)
            await self.db_session.commit()
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

    async def get_project_id_by_external_id(self, external_project_id: int) -> Optional[int]:
        # should be renamed external_id instead of internal_id, and be an integer not a string
        query = select(Project.id).where(Project.internal_id == cast(str(external_project_id), String))
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: int) -> List[Project]:
        query = select(Project).join(user_project_association).where(user_project_association.c.user_id == user_id)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_by_internal_id(self, internal_id: str) -> Project:
        stmt = select(Project).where(Project.internal_id == internal_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
