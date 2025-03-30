from pydantic_settings import BaseSettings


class OpenAiSettings(BaseSettings):
    openai_api_key: str
    openai_model: str
    openai_embedding_model: str
    openai_timeout_seconds: int


class GeminiSettings(BaseSettings):
    gemini_api_key: str


openai_settings = OpenAiSettings()
gemini_settings = GeminiSettings()
