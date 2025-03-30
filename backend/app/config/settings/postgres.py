from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class PostgresSettings(BaseSettings):
    postgres_url: PostgresDsn
