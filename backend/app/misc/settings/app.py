from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
	origin_url: HttpUrl


app_settings = AppSettings()
