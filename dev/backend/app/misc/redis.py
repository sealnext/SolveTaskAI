from redis.asyncio import Redis, from_url
from redis.backoff import ExponentialBackoff
from redis.exceptions import (
	ConnectionError as RedisConnectionError,
)
from redis.exceptions import (
	TimeoutError as RedisTimeoutError,
)
from redis.retry import Retry

from app.misc.settings import settings

redis: Redis = from_url(
	url=str(settings.redis_url),
	retry=Retry(ExponentialBackoff(cap=10, base=1), 25),
	retry_on_error=[RedisConnectionError, RedisTimeoutError, ConnectionResetError],
	health_check_interval=1,
)
