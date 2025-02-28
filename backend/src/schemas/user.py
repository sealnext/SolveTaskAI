from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserPassword(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserCreate(UserPassword):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @validator('email')
    def email_domain(cls, v):
        domain = v.split('@')[1]
        if domain in ['example.com', 'test.com']:
            raise ValueError('This email domain is not allowed')
        return v


class UserRead(BaseModel):
    id: Optional[int]
    username: str
    email: EmailStr

    class Config:
        from_attributes = True