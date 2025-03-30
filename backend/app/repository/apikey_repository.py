from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.model.api_key import APIKeyDB
from app.schema.api_key import APIKey
from typing import List, Optional
from app.misc.enums import TicketingSystemType
from sqlalchemy.exc import IntegrityError
from app.model.associations import api_key_project_association


class APIKeyRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_project_id(self, project_id: int) -> APIKeyDB | None:
        result = await self.db_session.execute(
            select(APIKeyDB)
            .join(api_key_project_association)
            .where(api_key_project_association.c.project_id == project_id)
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKey.from_orm(api_key_obj)
        return None

    async def create_api_key(self, api_key: APIKeyDB) -> APIKeyDB:
        try:
            self.db_session.add(api_key)
            await self.db_session.flush()
            await self.db_session.refresh(api_key)
            await self.db_session.commit()
            return api_key
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                await self.db_session.rollback()
                await self.db_session.execute(
                    text(
                        "SELECT setval('api_keys_id_seq', (SELECT MAX(id) FROM api_keys))"
                    )
                )
                api_key.id = None  # Reset the ID to let the database assign a new one
                return await self.create_api_key(api_key)
            raise

    async def delete_api_key(self, user_id: int, api_key_id: int) -> None:
        api_key = await self.get_by_id(api_key_id, user_id)
        if api_key:
            await self.db_session.delete(api_key)
            await self.db_session.commit()

    async def get_api_keys_by_user(self, user_id: int) -> List[APIKey]:
        result = await self.db_session.execute(
            select(APIKeyDB).where(APIKeyDB.user_id == user_id)
        )
        api_keys = result.scalars().all()
        return [APIKey.from_orm(api_key) for api_key in api_keys]

    async def get_by_id(self, api_key_id: int, user_id: int) -> APIKeyDB | None:
        result = await self.db_session.execute(
            select(APIKeyDB).where(
                (APIKeyDB.id == api_key_id) & (APIKeyDB.user_id == user_id)
            )
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKey.from_orm(api_key_obj)
        return None

    async def get_api_key_by_user_and_project(
        self, user_id: int, project_id: int
    ) -> APIKeyDB | None:
        result = await self.db_session.execute(
            select(APIKeyDB).where(
                (APIKeyDB.user_id == user_id) & (APIKeyDB.project_id == project_id)
            )
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKey.from_orm(api_key_obj)
        return None

    async def get_api_key_by_user_and_service(
        self, user_id: int, service_type: TicketingSystemType
    ) -> APIKeyDB | None:
        result = await self.db_session.execute(
            select(APIKeyDB).where(
                (APIKeyDB.user_id == user_id) & (APIKeyDB.service_type == service_type)
            )
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKey.from_orm(api_key_obj)
        return None

    async def get_api_key_by_value(self, api_key_value: str) -> Optional[APIKey]:
        result = await self.db_session.execute(
            select(APIKeyDB).where(APIKeyDB.api_key == api_key_value)
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKey.from_orm(api_key_obj)
        return None
