from pydantic_settings import BaseSettings


class JiraSettings(BaseSettings):
    jira_url: str
    jira_username: str
    jira_password: str


jira_settings = JiraSettings()
