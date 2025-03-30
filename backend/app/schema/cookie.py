from pydantic import BaseModel


class CookieSettings(BaseModel):
    key: str
    value: str
    max_age: int
    httponly: bool = True
    secure: bool = True
    samesite: str = "lax"
