import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from models import Base
from db.session import engine

async def sync_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def sync_database():
    await sync_db()

if __name__ == "__main__":
    sync_database()