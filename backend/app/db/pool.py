from typing import Optional, AsyncContextManager, Type
from types import TracebackType
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.config.config import DATABASE_URL
from logging import getLogger


logger = getLogger(__name__)


class DatabasePool(AsyncContextManager["DatabasePool"]):
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None
        self.checkpointer: Optional[AsyncPostgresSaver] = None

    async def __aenter__(self) -> "DatabasePool":
        """Async context manager entry."""
        if not self.pool:
            await self.create_pool()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit."""
        await self.close_pool()

    async def create_pool(self) -> None:
        """Create and initialize the connection pool."""
        if self.pool is None:
            # In case the database url from env is with psycopg, we need to remove the psycopg prefix
            # there is a difference between SqlAlchemy and Sql normal connection
            db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            try:
                self.pool = AsyncConnectionPool(
                    conninfo=db_url,
                    max_size=20,
                    min_size=4,
                    open=False,
                    kwargs={"autocommit": True, "prepare_threshold": 0},
                )
                await self.pool.open()
                logger.info("PostgreSQL connection pool opened")

                # Create and setup checkpointer
                await self.setup_checkpointer()
            except Exception as e:
                logger.error(f"Failed to create pool: {e}")
                if self.pool:
                    await self.close_pool()
                raise

    async def setup_checkpointer(self) -> None:
        """Initialize the checkpointer with proper async context management."""
        if self.pool is None:
            raise RuntimeError("Pool must be created before setting up checkpointer")

        try:
            self.checkpointer = AsyncPostgresSaver(self.pool)
            await self.checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")
        except Exception as e:
            logger.error(f"Failed to setup checkpointer: {e}")
            await self.close_pool()  # Cleanup on error
            raise

    async def get_checkpointer(self) -> AsyncPostgresSaver:
        """Get the checkpointer instance, ensuring it's properly initialized."""
        if self.checkpointer is None:
            await self.setup_checkpointer()
        if self.checkpointer is None:  # Double check after setup
            raise RuntimeError("Failed to initialize checkpointer")
        return self.checkpointer

    async def close_pool(self) -> None:
        """Close the connection pool and cleanup resources."""
        if self.checkpointer:
            self.checkpointer = None
            logger.info("PostgreSQL checkpointer reference removed")

        if self.pool and not self.pool.closed:
            try:
                await self.pool.close()
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
                raise  # Re-raise to ensure error is propagated
            finally:
                self.pool = None


# Global instance
db_pool = DatabasePool()
