from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.misc.logger import logger
from app.misc.settings import settings


class DatabasePool:
	def __init__(self):
		self.pool: AsyncConnectionPool | None = None
		self.checkpointer: AsyncPostgresSaver | None = None

	async def initialize(self) -> None:
		"""Create the connection pool and initialize the checkpointer."""
		if self.pool is not None:
			logger.warning('Database pool already initialized.')
			return

		db_url = str(settings.postgres_url)
		db_url = db_url.replace('+psycopg', '')
		db_url = db_url.replace('+asyncpg', '')

		try:
			self.pool = AsyncConnectionPool(
				conninfo=db_url,
				max_size=20,
				min_size=1,
				open=False,
			)
			await self.pool.open()
			logger.info('PostgreSQL connection pool opened')

			self.checkpointer = AsyncPostgresSaver(self.pool)
			await self.checkpointer.setup()
			logger.info('PostgreSQL checkpointer initialized')

		except Exception as e:
			logger.error(f'Failed to initialize database pool or checkpointer: {e}')
			await self.close()
			raise

	async def get_checkpointer(self) -> AsyncPostgresSaver:
		"""Get the checkpointer instance. Assumes initialize() has been called."""
		if self.checkpointer is None:
			logger.error('Checkpointer accessed before initialization.')
			raise RuntimeError('Checkpointer not initialized. Check lifespan management.')
		return self.checkpointer

	async def close(self) -> None:
		"""Close the connection pool and cleanup resources."""
		if self.checkpointer:
			self.checkpointer = None
			logger.info('PostgreSQL checkpointer reference removed')

		if self.pool and not self.pool.closed:
			try:
				await self.pool.close()
				logger.info('PostgreSQL connection pool closed')
			except Exception as e:
				logger.error(f'Error closing pool: {e}')
			finally:
				self.pool = None
		elif self.pool:
			self.pool = None


# Global instance
langgraph_db_pool = DatabasePool()
