from redis.asyncio import Redis, from_url

from app.misc.settings import settings

redis: Redis = from_url(url=str(settings.redis_url))
