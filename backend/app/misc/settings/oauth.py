from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='GOOGLE_')

	client_id: str
	client_secret: str


class GithubSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='GITHUB_')

	client_id: str
	client_secret: str


google_settings = GoogleSettings()
github_settings = GithubSettings()
