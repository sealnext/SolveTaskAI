from typing import List
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.api_key import APIKeyDB
from app.model.project import ProjectDB
from app.model.associations import api_key_project_association
from app.schema.api_key import APIKey
from app.misc.enums import TicketingSystemType


class APIKeyRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, api_key_id: int) -> APIKey | None:
        stmt = select(APIKeyDB).where(APIKeyDB.id == api_key_id)
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None

    async def get_by_value(self, api_key_value: str) -> APIKey | None:
        stmt = select(APIKeyDB).where(APIKeyDB.api_key == api_key_value)
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None

    async def get_by_project_id_and_user(
        self, project_id: int, user_id: int
    ) -> APIKey | None:
        stmt = (
            select(APIKeyDB)
            .join(api_key_project_association)
            .where(
                (api_key_project_association.c.project_id == project_id)
                & (APIKeyDB.user_id == user_id)
            )
        )
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None

    async def get_api_keys_by_user(self, user_id: int) -> List[APIKey]:
        stmt = select(APIKeyDB).where(APIKeyDB.user_id == user_id)
        result = await self.db_session.execute(stmt)
        db_keys = result.scalars().all()
        return [APIKey.model_validate(key) for key in db_keys]

    async def get_api_key_by_user_and_project(
        self, user_id: int, project_id: int
    ) -> APIKey | None:
        stmt = (
            select(APIKeyDB)
            .join(api_key_project_association)
            .where(
                (APIKeyDB.user_id == user_id)
                & (api_key_project_association.c.project_id == project_id)
            )
        )
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None

    async def get_api_key_by_user_and_service(
        self, user_id: int, service_type: TicketingSystemType
    ) -> APIKey | None:
        stmt = select(APIKeyDB).where(
            (APIKeyDB.user_id == user_id) & (APIKeyDB.service_type == service_type)
        )
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None

    async def create_api_key(
        self,
        user_id: int,
        api_key_value: str,
        service_type: TicketingSystemType,
        domain: str,
        domain_email: str,
        project_ids: List[int],
        expires_at: datetime | None = None,
    ) -> APIKey:
        project_stmt = select(ProjectDB).where(ProjectDB.id.in_(project_ids))
        project_result = await self.db_session.execute(project_stmt)
        projects = project_result.scalars().all()
        if len(projects) != len(project_ids):
            found_ids = {p.id for p in projects}
            missing_ids = set(project_ids) - found_ids
            # TODO: Consider logging a warning or raising an error
            print(f"Warning: Projects not found for IDs: {missing_ids}")

        db_key = APIKeyDB(
            user_id=user_id,
            api_key=api_key_value,
            service_type=service_type,
            domain=domain,
            domain_email=domain_email,
            expires_at=expires_at,
            projects=projects,
        )

        self.db_session.add(db_key)
        await self.db_session.flush()
        await self.db_session.refresh(db_key, attribute_names=["id", "created_at"])
        await self.db_session.refresh(db_key, attribute_names=["projects"])

        return APIKey.model_validate(db_key)

    async def delete_api_key(self, api_key_id: int) -> bool:
        stmt_select = select(APIKeyDB).where(APIKeyDB.id == api_key_id)
        result = await self.db_session.execute(stmt_select)
        db_key = result.scalar_one_or_none()

        if db_key:
            await self.db_session.delete(db_key)
            return True
        return False

    async def get_by_id_and_user(self, api_key_id: int, user_id: int) -> APIKey | None:
        stmt = select(APIKeyDB).where(
            (APIKeyDB.id == api_key_id) & (APIKeyDB.user_id == user_id)
        )
        result = await self.db_session.execute(stmt)
        db_key = result.scalar_one_or_none()
        return APIKey.model_validate(db_key) if db_key else None
