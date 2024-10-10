from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.apikey import APIKey

async def get_api_key_by_user_and_project(db: AsyncSession, user_id: int, project_id: int) -> APIKey | None:
    result = await db.execute(
        select(APIKey).where(
            (APIKey.user_id == user_id) & (APIKey.project_id == project_id)
        )
    )
    return result.scalar_one_or_none()
