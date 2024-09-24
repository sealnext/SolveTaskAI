from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.user_repository import UserRepository
from services.user_service import UserService
from services.auth_service import AuthService

async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db_session=db)

# Singleton instances
# TODO: NEEDS TO BE FIXED : AttributeError: 'function' object has no attribute 'get_by_email'
user_service_instance = UserService(get_user_repository)
auth_service_instance = AuthService()

def get_user_service():
    return user_service_instance

def get_auth_service():
    return auth_service_instance

