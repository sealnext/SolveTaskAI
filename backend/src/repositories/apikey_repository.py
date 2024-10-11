from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.apikey import APIKey
from typing import List

class APIKeyRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_api_key(self, api_key: APIKey) -> APIKey:
        self.db_session.add(api_key)
        await self.db_session.commit()
        return api_key

    async def delete_api_key(self, api_key: APIKey) -> None:
        await self.db_session.delete(api_key)
        await self.db_session.commit()

    async def get_api_keys_by_user(self, user_id: int) -> List[APIKey]:
        result = await self.db_session.execute(
            select(APIKey).where(APIKey.user_id == user_id)
        )
        return result.scalars().all()

    async def get_api_key_by_user_and_project(self, user_id: int, project_id: int) -> APIKey | None:
        result = await self.db_session.execute(
            select(APIKey).where(
                (APIKey.user_id == user_id) & (APIKey.project_id == project_id)
            )
        )
        return result.scalar_one_or_none()
