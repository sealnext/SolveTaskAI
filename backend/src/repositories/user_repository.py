from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from schemas import UserCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from exceptions import UserAlreadyExistsException

class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_email(self, email: str) -> User:
        query = select(User).where(User.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_create: UserCreate) -> User:
        new_user = User(
            email=user_create.email,
            full_name=user_create.username, 
            hashed_password=user_create.password
        )
        self.db_session.add(new_user)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(new_user)
        except IntegrityError:
            await self.db_session.rollback()
            raise UserAlreadyExistsException
        
        return new_user

    async def get_by_id(self, user_id: int) -> User:
        query = select(User).where(User.id == user_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
