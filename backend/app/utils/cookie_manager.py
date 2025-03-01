from fastapi.responses import Response
from app.schemas.cookie import CookieSettings
from datetime import timedelta
from typing import Optional
from app.config.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_expires: Optional[int] = None,
    refresh_token_expires: Optional[int] = None,
) -> None:
    access_token_settings = CookieSettings(
        key="access_token",
        value=access_token,
        max_age=int(
            timedelta(
                minutes=access_token_expires or JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            ).total_seconds()
        ),
    )

    refresh_token_settings = CookieSettings(
        key="refresh_token",
        value=refresh_token,
        max_age=int(
            timedelta(
                days=refresh_token_expires or JWT_REFRESH_TOKEN_EXPIRE_DAYS
            ).total_seconds()
        ),
    )

    for cookie in [access_token_settings, refresh_token_settings]:
        response.set_cookie(**cookie.dict())
