from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.user_repository import UserRepository
from services import UserService
from services import AuthService
from repositories import APIKeyRepository

@lru_cache()
def get_auth_service():
    return AuthService()

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

async def get_api_key_repository(db: AsyncSession = Depends(get_db)):
    return APIKeyRepository(db_session=db)

async def get_user_service(repo: UserRepository = Depends(get_user_repository), api_key_repo: APIKeyRepository = Depends(get_api_key_repository)):
    return UserService(repo, api_key_repo)
