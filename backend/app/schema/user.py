from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserCreate(BaseModel):
    """Schema for creating a new user, with validation."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    model_config = {}

    @field_validator("username", mode="after")
    @classmethod
    def validate_username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> EmailStr:
        domain = v.split("@")[1]
        if domain in ["example.com", "test.com"]:
            raise ValueError("This email domain is not allowed")
        return v

    @field_validator("password", mode="after")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserRead(BaseModel):
    """Schema for reading user data."""

    id: int
    full_name: str
    email: EmailStr

    model_config = {"from_attributes": True}
