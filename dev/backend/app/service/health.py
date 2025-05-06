import sqlalchemy
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.misc.logger import logger
from app.misc.redis import redis


class HealthService:
	def __init__(self, async_db_session: AsyncSession):
		self.async_db_session = async_db_session

	@staticmethod
	async def check_redis_health() -> bool:
		try:
			return await redis.ping()
		except redis.exceptions.ConnectionError as e:
			logger.error("Can't connect to Redis: %s", e)
			return False
		except redis.exceptions.TimeoutError as e:
			logger.error('Redis connection timed out: %s', e)
			return False
		except redis.exceptions.RedisError as e:
			logger.error('Redis error: %s', e)
			return False
		except Exception as e:
			logger.exception('Unexpected error while pinging Redis: %s', e)
			return False

	async def check_db_health(self) -> bool:
		try:
			result = await self.async_db_session.execute(text('SELECT 1'))
			returned_value = result.scalar_one()
			return returned_value == 1
		except sqlalchemy.exc.SQLAlchemyError as e:
			logger.error('SQLAlchemy error: %s', e)
			return False
		except Exception as e:
			logger.exception('Unexpected error while executing DB health check: %s', e)
			return False
