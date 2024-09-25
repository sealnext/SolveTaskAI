from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.user_repository import UserRepository
from services.user_service import UserService
from services.auth_service import AuthService

@lru_cache()
def get_auth_service():
    return AuthService()

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

async def get_user_service(repo: UserRepository = Depends(get_user_repository)):
    return UserService(repo)

