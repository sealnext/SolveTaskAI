from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update

from app.model.user import UserDB
from app.schema.user import UserCreate


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_email(self, email: str) -> UserDB:
        query = select(UserDB).where(UserDB.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> UserDB:
        query = select(UserDB).where(UserDB.id == user_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_create: UserCreate) -> UserDB:
        new_user = UserDB(
            email=user_create.email,
            full_name=user_create.username,
            hashed_password=user_create.password,
        )
        self.db_session.add(new_user)

        try:
            await self.db_session.commit()
            await self.db_session.refresh(new_user)
        except IntegrityError:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        return new_user

    async def update_password(self, user_id: int, new_password: str) -> None:
        query = (
            update(UserDB)
            .where(UserDB.id == user_id)
            .values(hashed_password=new_password)
        )
        await self.db_session.execute(query)
        await self.db_session.commit()
