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

VECTOR_DIMENSION = os.getenv("VECTOR_DIMENSION", 1536)