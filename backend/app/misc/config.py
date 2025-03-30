import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
NUMBER_OF_DOCS_TO_RETRIEVE = int(os.getenv("NUMBER_OF_DOCS_TO_RETRIEVE", 5))

OPENAI_TIMEOUT_SECONDS = int(
    os.getenv("OPENAI_TIMEOUT_SECONDS", "30")
)  # Timeout for OpenAI API calls in seconds
# Document processing settings
CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", "10000")
)  # Number of documents to process in memory at once

# Jira API settings
JIRA_MAX_CONCURRENT_REQUESTS = int(
    os.getenv("JIRA_MAX_CONCURRENT_REQUESTS", "5")
)  # Maximum concurrent requests to Jira
JIRA_MAX_RESULTS_PER_PAGE = int(
    os.getenv("JIRA_MAX_RESULTS_PER_PAGE", "1000")
)  # Maximum results per Jira API request
JIRA_API_VERSION = int(os.getenv("JIRA_API_VERSION", "2"))  # Jira API version

DEFAULT_REQUEST_TIMEOUT = int(
    os.getenv("DEFAULT_REQUEST_TIMEOUT", "45")
)  # Default request timeout in seconds
