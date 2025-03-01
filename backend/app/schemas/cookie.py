from pydantic import BaseModel, Field
from app.config.config import ENVIRONMENT


class CookieSettings(BaseModel):
    key: str
    value: str
    max_age: int
    httponly: bool = True
    secure: bool = Field(default_factory=lambda: ENVIRONMENT == "production")
    samesite: str = "lax"
