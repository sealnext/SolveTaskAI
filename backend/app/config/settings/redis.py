from pydantic_settings import BaseSettings
from pydantic import RedisDsn


class RedisSettings(BaseSettings):
    redis_url: RedisDsn
