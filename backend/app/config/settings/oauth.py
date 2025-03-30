from pydantic_settings import BaseSettings


class GoogleSettings(BaseSettings):
    google_client_id: str
    google_client_secret: str


class GithubSettings(BaseSettings):
    github_client_id: str
    github_client_secret: str
