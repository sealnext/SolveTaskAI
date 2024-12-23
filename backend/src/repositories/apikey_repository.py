from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from models.apikey import APIKey
from schemas import APIKeySchema
from typing import List, Optional
from config.enums import TicketingSystemType
from sqlalchemy.exc import IntegrityError
from models.associations import api_key_project_association

class APIKeyRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        
    async def get_by_project_id(self, project_id: int) -> APIKeySchema | None:
        result = await self.db_session.execute(
            select(APIKey).join(api_key_project_association).where(api_key_project_association.c.project_id == project_id)
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj:
            return APIKeySchema.from_orm(api_key_obj)
        return None
    
    async def create_api_key(self, api_key: APIKey) -> APIKey:
        try:
            self.db_session.add(api_key)
            await self.db_session.flush()
            await self.db_session.refresh(api_key)
            await self.db_session.commit()
            return api_key
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                await self.db_session.rollback()
                await self.db_session.execute(text("SELECT setval('api_keys_id_seq', (SELECT MAX(id) FROM api_keys))"))
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
            select(APIKey).where(APIKey.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_id(self, api_key_id: int, user_id: int) -> APIKey | None:
        result = await self.db_session.execute(
            select(APIKey).where(
                (APIKey.id == api_key_id) & (APIKey.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_api_key_by_user_and_project(self, user_id: int, project_id: int) -> APIKey | None:
        result = await self.db_session.execute(
            select(APIKey).where(
                (APIKey.user_id == user_id) & (APIKey.project_id == project_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_api_key_by_user_and_service(self, user_id: int, service_type: TicketingSystemType) -> APIKey | None:
        result = await self.db_session.execute(
            select(APIKey).where(
                (APIKey.user_id == user_id) & (APIKey.service_type == service_type)
            )
        )
        return result.scalar_one_or_none()

    async def get_api_key_by_value(self, api_key_value: str) -> Optional[APIKey]:
        result = await self.db_session.execute(
            select(APIKey).where(APIKey.api_key == api_key_value)
        )
        return result.scalar_one_or_none()
