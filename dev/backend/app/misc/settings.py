from base64 import b64decode
from typing import Annotated

from pydantic import (
	AfterValidator,
	BeforeValidator,
	HttpUrl,
	PostgresDsn,
	RedisDsn,
	SecretBytes,
	SecretStr,
)
from pydantic_settings import BaseSettings


def _validate_url_https(url: HttpUrl) -> HttpUrl:
	str_url = str(url)
	if (
		str_url.startswith('https://')
		or str_url == 'http://localhost/'
		or str_url == 'http://127.0.0.1/'
	):
		return url
	raise ValueError(f'Invalid URL {str_url} (must start with https:// or be http://localhost/)')


HttpsUrl = Annotated[HttpUrl, AfterValidator(_validate_url_https)]


class Settings(BaseSettings):
	origin_url: HttpsUrl

	email_verification_token_length: int = 32
	email_verification_ttl: int = 24 * 60 * 60  # 24 hours

	session_token_length: int = 32
	session_ttl: int = 7 * 24 * 60 * 60  # 7 days

	postgres_url: PostgresDsn
	redis_url: RedisDsn

	jira_max_concurrent_requests: int = 5
	jira_max_results_per_page: int = 1000
	jira_api_version: int = 2
	jira_number_of_docs_to_retrieve: int = 5

	openai_api_key: SecretStr
	openai_model: str = 'gpt-4o-mini'
	openai_embedding_model: str = 'text-embedding-3-small'

	google_api_key: SecretStr
	google_model: str = 'gemini-2.0-flash'

	oauth_github_client_id: str
	oauth_github_client_secret: SecretStr
	oauth_github_auth_url: HttpUrl = 'https://github.com/login/oauth/authorize'
	oauth_github_access_token_url: HttpsUrl = 'https://github.com/login/oauth/access_token'

	oauth_google_client_id: str
	oauth_google_client_secret: SecretStr
	oauth_google_auth_url: HttpsUrl = 'https://accounts.google.com/o/oauth2/v2/auth'
	oauth_google_access_token_url: HttpsUrl = 'https://oauth2.googleapis.com/token'

	encryption_key: Annotated[
		SecretBytes, BeforeValidator(lambda key: b64decode(key, validate=True))
	]

	email_api_key: SecretStr


settings = Settings()
