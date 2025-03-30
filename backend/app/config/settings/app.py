from pydantic_settings import BaseSettings
from pydantic import HttpUrl


class AppSettings(BaseSettings):
    origin_url: HttpUrl
