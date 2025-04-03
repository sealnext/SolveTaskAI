from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='POSTGRES_')

	url: PostgresDsn


class RedisSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='REDIS_')

	url: RedisDsn


postgres_settings = PostgresSettings()
redis_settings = RedisSettings()
