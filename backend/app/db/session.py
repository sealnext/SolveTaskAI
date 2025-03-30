from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


class DBState:
    count = 0


# Use it like this
DBState.count += 1
logger.info(f"count: {DBState.count}")

logger.info(f"DATABASE_URL: {DATABASE_URL}")
engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    logger.info("Initializing pgvector database...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
