import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

DATABASE_URL = os.getenv("DATABASE_URL")
SYNC_DATABASE = os.getenv("SYNC_DATABASE", "False").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
SQL_LOGGING = os.getenv("SQL_LOGGING", "false").lower() == "true"

VECTOR_DIMENSION = os.getenv("VECTOR_DIMENSION", 1536)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
NUMBER_OF_DOCS_TO_RETRIEVE = int(os.getenv("NUMBER_OF_DOCS_TO_RETRIEVE", 5))

# OpenAI rate limiting and batch settings
OPENAI_MAX_BATCH_SIZE = int(
    os.getenv("OPENAI_MAX_BATCH_SIZE", "2048")
)  # Maximum texts OpenAI can process in one request
OPENAI_REQUESTS_PER_MINUTE = int(
    os.getenv("OPENAI_REQUESTS_PER_MINUTE", "500")
)  # OpenAI's rate limit for embeddings
OPENAI_MAX_RETRIES = int(
    os.getenv("OPENAI_MAX_RETRIES", "3")
)  # Maximum number of retries for OpenAI API calls
OPENAI_RETRY_DELAY = int(
    os.getenv("OPENAI_RETRY_DELAY", "1")
)  # Initial delay between retries in seconds
OPENAI_TIMEOUT_SECONDS = int(
    os.getenv("OPENAI_TIMEOUT_SECONDS", "30")
)  # Timeout for OpenAI API calls in seconds
# Document processing settings
CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", "10000")
)  # Number of documents to process in memory at once
DB_BATCH_SIZE = int(
    os.getenv("DB_BATCH_SIZE", "500")
)  # Number of documents to insert into DB at once

# Jira API settings
JIRA_MAX_CONCURRENT_REQUESTS = int(
    os.getenv("JIRA_MAX_CONCURRENT_REQUESTS", "5")
)  # Maximum concurrent requests to Jira
JIRA_MAX_RESULTS_PER_PAGE = int(
    os.getenv("JIRA_MAX_RESULTS_PER_PAGE", "1000")
)  # Maximum results per Jira API request
JIRA_API_VERSION = int(os.getenv("JIRA_API_VERSION", "2"))  # Jira API version
JIRA_RETRY_ATTEMPTS = int(
    os.getenv("JIRA_RETRY_ATTEMPTS", "3")
)  # Number of retry attempts for failed Jira requests
JIRA_RETRY_DELAY = int(
    os.getenv("JIRA_RETRY_DELAY", "1")
)  # Initial delay between Jira retries in seconds

DEFAULT_REQUEST_TIMEOUT = int(
    os.getenv("DEFAULT_REQUEST_TIMEOUT", "45")
)  # Default request timeout in seconds
