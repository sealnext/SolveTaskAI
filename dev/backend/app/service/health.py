from logging import getLogger

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.misc.redis import redis


logger = getLogger(__name__)


class HealthService:
	def __init__(self, async_db_session: AsyncSession):
		self.async_db_session = async_db_session

	@staticmethod
	async def check_redis_health() -> bool:
		try:
			return await redis.ping()
		except Exception as e:
			logger.error(f'Error pinging Redis: {e}')
		return False

	async def check_db_health(self) -> bool:
		try:
			result = await self.async_db_session.execute(text('SELECT 1'))
			returned_value = result.scalar_one()
			return returned_value == 1
		except Exception as e:
			logger.error(f'Error executing DB health check: {e}')
		return False
