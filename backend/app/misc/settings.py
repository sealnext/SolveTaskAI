from pydantic import HttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	origin_url: HttpUrl

	session_token_length: int = 32
	session_ttl: int = 7 * 24 * 60 * 60  # TTL = Time To Live (seconds)

	postgres_url: PostgresDsn
	redis_url: RedisDsn

	jira_max_concurrent_requests: int = 5
	jira_max_results_per_page: int = 1000
	jira_api_version: int = 2
	jira_number_of_docs_to_retrieve: int = 5

	openai_api_key: str
	openai_model: str = 'gpt-4o-mini'
	openai_embedding_model: str = 'text-embedding-3-small'

	google_api_key: str
	google_model: str = 'gemini-2.0-flash'

	oauth_github_client_id: str
	oauth_github_client_secret: str
	oauth_github_auth_url: str = 'https://github.com/login/oauth/authorize'
	oauth_github_access_token_url: HttpUrl = 'https://github.com/login/oauth/access_token'

	oauth_google_client_id: str
	oauth_google_client_secret: str
	oauth_google_auth_url: HttpUrl = 'https://accounts.google.com/o/oauth2/v2/auth'
	oauth_google_access_token_url: HttpUrl = 'https://oauth2.googleapis.com/token'


settings = Settings()
