from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAiSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='OPENAI_')

	api_key: str
	model: str
	embedding_model: str
	timeout_seconds: int


class GeminiSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='GEMINI_')

	api_key: str


openai_settings = OpenAiSettings()
gemini_settings = GeminiSettings()
