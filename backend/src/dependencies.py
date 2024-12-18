from repositories import ChatSessionRepository
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.user_repository import UserRepository
from services import UserService
from services import AuthService
from repositories import APIKeyRepository
from repositories import ProjectRepository
from services import ProjectService
from services import APIKeyService
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from db.pool import db_pool

# User dependencies
async def get_api_key_repository(db: AsyncSession = Depends(get_db)):
    return APIKeyRepository(db_session=db)

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

async def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository)
):
    return UserService(repo, api_key_repo)

async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)):
    return AuthService(user_repo)

# Project dependencies
async def get_project_repository(db: AsyncSession = Depends(get_db)):
    return ProjectRepository(db)

async def get_project_service(project_repo: ProjectRepository = Depends(get_project_repository)):
    return ProjectService(project_repo)

async def get_apikey_service(repo: APIKeyRepository = Depends(get_api_key_repository)):
    return APIKeyService(repo)

async def get_chat_session_repository(db: AsyncSession = Depends(get_db)):
    return ChatSessionRepository(db)

# Checkpointer dependency
async def get_db_checkpointer() -> AsyncPostgresSaver:
    """FastAPI dependency for getting the checkpointer."""
    if db_pool.checkpointer is None:
        await db_pool.create_pool()
    return db_pool.checkpointer