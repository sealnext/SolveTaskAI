from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserRead(BaseModel):
    id: Optional[uuid.UUID]
    username: str
    email: EmailStr

    class Config:
        from_attributes = True