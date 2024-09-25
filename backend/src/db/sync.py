import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from models import Base
from db.session import engine
from config import SYNC_DATABASE

async def sync_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def sync_database():
    if SYNC_DATABASE:
        await sync_db()
    else:
        print("Database synchronization is disabled.")

if __name__ == "__main__":
    asyncio.run(sync_database())