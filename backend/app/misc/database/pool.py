from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.misc.config import DATABASE_URL
from logging import getLogger


logger = getLogger(__name__)


class DatabasePool:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None
        self.checkpointer: Optional[AsyncPostgresSaver] = None

    async def initialize(self) -> None:
        """Create the connection pool and initialize the checkpointer."""
        if self.pool is not None:
            logger.warning("Database pool already initialized.")
            return

        db_url = DATABASE_URL
        if db_url.startswith("postgresql+psycopg://"):
            db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
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

            self.checkpointer = AsyncPostgresSaver(self.pool)
            await self.checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database pool or checkpointer: {e}")
            # Ensure cleanup on initialization error
            await self.close()
            raise

    async def get_checkpointer(self) -> AsyncPostgresSaver:
        """Get the checkpointer instance. Assumes initialize() has been called."""
        if self.checkpointer is None:
            # This should ideally not happen if initialize() is called correctly by lifespan
            logger.error("Checkpointer accessed before initialization.")
            raise RuntimeError(
                "Checkpointer not initialized. Check lifespan management."
            )
        return self.checkpointer

    async def close(self) -> None:
        """Close the connection pool and cleanup resources."""
        # Reset checkpointer reference first
        if self.checkpointer:
            self.checkpointer = None
            logger.info("PostgreSQL checkpointer reference removed")

        if self.pool and not self.pool.closed:
            try:
                await self.pool.close()
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
                # Log error but don't necessarily prevent pool variable reset
            finally:
                # Ensure pool is marked as None even if close fails
                self.pool = None
        elif self.pool:  # If pool exists but was already closed
            self.pool = None


# Global instance
db_pool = DatabasePool()
