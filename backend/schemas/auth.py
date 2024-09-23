from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

# Token schema for authentication responses
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for user creation (input validation)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # Email validation
    password: str = Field(..., min_length=8, max_length=128)

# Optional response schema for user read operations
class UserRead(BaseModel):
    id: Optional[uuid.UUID]
    username: str
    email: EmailStr

    class Config:
        orm_mode = True  # Enables automatic conversion from ORM objects
