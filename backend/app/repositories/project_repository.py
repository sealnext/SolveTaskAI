from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, cast, String, insert
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from app.models.project import ProjectDB
from app.models.user import UserDB
from app.models.associations import (
    user_project_association,
    api_key_project_association,
)
from app.models.chat_session import ChatSession
from app.schemas.project import ProjectUpdate, ProjectCreate
from app.exceptions.custom_exceptions import ProjectAlreadyExistsError


async def get_project_repository(db_session: AsyncSession):
    return ProjectRepository(db_session)


class ProjectRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_external_id(
        self, user_id: int, external_project_id: int
    ) -> Optional[ProjectDB]:
        query = (
            select(ProjectDB)
            .join(user_project_association)
            .where(
                and_(
                    ProjectDB.internal_id == cast(str(external_project_id), String),
                    user_project_association.c.user_id == user_id,
                )
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: int, project: ProjectCreate) -> ProjectDB:
        try:
            # Check if project already exists
            existing_project = await self.get_by_internal_id(project.internal_id)
            if existing_project:
                raise ProjectAlreadyExistsError(
                    f"Contextual project already exist for this project"
                )

            api_key_id = project.api_key_id
            project_data = project.model_dump(exclude={"api_key_id"})

            db_project = ProjectDB(**project_data)
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
            stmt = (
                select(ProjectDB)
                .options(
                    selectinload(ProjectDB.api_keys), selectinload(ProjectDB.users)
                )
                .where(ProjectDB.id == db_project.id)
            )
            result = await self.db_session.execute(stmt)
            db_project = result.scalar_one()

            await self.db_session.commit()

            return db_project
        except IntegrityError as e:
            await self.db_session.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                raise ProjectAlreadyExistsError(
                    f"Project with these details already exists: {str(e)}"
                )
            raise

    async def create_with_retry(
        self, user_id: int, project: ProjectCreate
    ) -> ProjectDB:
        try:
            return await self.create(user_id, project)
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                await self.db_session.rollback()
                return await self.create_with_retry(user_id, project)
            raise

    async def get_by_id(self, user_id: int, project_id: int) -> Optional[ProjectDB]:
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

    async def update(
        self, user_id: int, project_id: int, project_update: ProjectUpdate
    ) -> Optional[ProjectDB]:
        project = await self.get_by_id(user_id, project_id)
        if project:
            for key, value in project_update.model_dump(exclude_unset=True).items():
                setattr(project, key, value)
            await self.db_session.flush()
            await self.db_session.refresh(project)
        return project

    async def delete(self, user_id: int, project_id: int):
        try:
            # Start a transaction
            async with self.db_session.begin_nested():
                # First delete chat sessions associated with the project
                await self.db_session.execute(
                    delete(ChatSession).where(ChatSession.project_id == project_id)
                )

                # Delete user-project associations
                await self.db_session.execute(
                    delete(user_project_association).where(
                        and_(
                            user_project_association.c.project_id == project_id,
                            user_project_association.c.user_id == user_id,
                        )
                    )
                )

                # Delete api-key-project associations
                await self.db_session.execute(
                    delete(api_key_project_association).where(
                        api_key_project_association.c.project_id == project_id
                    )
                )

                # Finally delete the project
                await self.db_session.execute(
                    delete(ProjectDB).where(ProjectDB.id == project_id)
                )

                await self.db_session.commit()
                return True
        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def get_with_related(
        self, user_id: int, project_id: int
    ) -> Optional[ProjectDB]:
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

    async def get_by_domain(self, user_id: int, domain: str) -> Optional[ProjectDB]:
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

    async def add_user_to_project(self, project_id: int, user_id: int) -> bool:
        project = await self.db_session.get(ProjectDB, project_id)
        user = await self.db_session.get(UserDB, user_id)
        if project and user:
            project.users.append(user)
            await self.db_session.commit()
            return True
        return False

    async def remove_user_from_project(self, project_id: int, user_id: int) -> bool:
        project = await self.db_session.get(ProjectDB, project_id)
        user = await self.db_session.get(UserDB, user_id)
        if project and user and user in project.users:
            project.users.remove(user)
            await self.db_session.commit()
            return True
        return False

    async def get_project_id_by_external_id(
        self, external_project_id: int
    ) -> Optional[int]:
        # should be renamed external_id instead of internal_id, and be an integer not a string
        query = select(ProjectDB.id).where(
            ProjectDB.internal_id == cast(str(external_project_id), String)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: int) -> List[ProjectDB]:
        query = (
            select(ProjectDB)
            .join(user_project_association)
            .where(user_project_association.c.user_id == user_id)
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_by_internal_id(self, internal_id: int) -> ProjectDB:
        # TODO: why tf is the internal_id an string in database? change it to int
        stmt = select(ProjectDB).where(ProjectDB.internal_id == str(internal_id))
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_project_associated(self, project_id: int) -> bool:
        query = select(user_project_association).where(
            user_project_association.c.project_id == project_id
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None
