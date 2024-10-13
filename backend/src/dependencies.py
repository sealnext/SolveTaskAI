from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.user_repository import UserRepository
from services import UserService
from services import AuthService
from repositories import APIKeyRepository
from repositories import ProjectRepository
from services import ProjectService
from db.session import get_db
from services import APIKeyService

# User dependencies

async def get_api_key_repository(db: AsyncSession = Depends(get_db)):
    return APIKeyRepository(db_session=db)

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

async def get_user_service(repo: UserRepository = Depends(get_user_repository), api_key_repo: APIKeyRepository = Depends(get_api_key_repository)):
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
