"""
Database connection pool management.
"""
import logging
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# TODO: Scalability considerations:
#  - For few users: current setup is fine (min=4, max=20)
#  - For hundreds of concurrent users: increase pool size (min=10, max=50)
#  - For thousands of users: consider implementing:
#    1. Connection pooling at proxy level (pgbouncer)
#    2. Read replicas for read-heavy operations
#    3. Database sharding for write-heavy operations

class DatabasePool:
    def __init__(self):
        self.pool = None
        self.checkpointer = None
        
    async def create_pool(self):
        """Create and initialize the connection pool."""
        if self.pool is None:
            db_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
            self.pool = AsyncConnectionPool(
                conninfo=db_url, 
                max_size=20, 
                min_size=4,  # Recommended in docs for better performance
                open=False
            )
            await self.pool.open()
            logger.info("PostgreSQL connection pool opened")
            
            # Initialize checkpointer
            self.checkpointer = AsyncPostgresSaver(self.pool)
            await self.checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")
    
    async def close_pool(self):
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
            finally:
                self.pool = None

# Global instance
db_pool = DatabasePool()