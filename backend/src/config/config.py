import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

DATABASE_URL = os.getenv("DATABASE_URL")
SYNC_DATABASE = os.getenv("SYNC_DATABASE", "False").lower() == "true"

NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
SQL_LOGGING = os.getenv("SQL_LOGGING", "false").lower() == "true"

VECTOR_DIMENSION = os.getenv("VECTOR_DIMENSION", 1536)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
NUMBER_OF_DOCS_TO_RETRIEVE = int(os.getenv("NUMBER_OF_DOCS_TO_RETRIEVE", 1))