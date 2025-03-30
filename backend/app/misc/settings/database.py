from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn


class PostgresSettings(BaseSettings):
    postgres_url: PostgresDsn


class RedisSettings(BaseSettings):
    redis_url: RedisDsn


postgres_settings = PostgresSettings()
redis_settings = RedisSettings()
