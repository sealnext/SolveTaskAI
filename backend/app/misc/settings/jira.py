from pydantic_settings import BaseSettings, SettingsConfigDict


class JiraSettings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix='JIRA_')

	max_concurrent_requests: int = 5
	max_results_per_page: int = 1000
	api_version: int = 2


jira_settings = JiraSettings()
