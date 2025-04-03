from redis.asyncio import from_url

from app.misc.settings import redis_settings

redis_client = from_url(str(redis_settings.url))
