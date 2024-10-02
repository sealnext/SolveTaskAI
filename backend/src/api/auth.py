import json
import logging
from datetime import timedelta

from jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_csrf_protect import CsrfProtect

from config import (
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    NEXTAUTH_SECRET,
)
from dependencies import get_auth_service, get_user_service
from exceptions import *
from services import AuthService, UserService
from utils.security import decode_next_auth_token
from validation_models import UserCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    access_token, refresh_token = await user_service.authenticate_and_get_tokens(
        form_data.username, form_data.password, request, auth_service
    )
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Login successful"}
    )
    auth_service.set_auth_cookies(response, access_token, refresh_token)

    return response


@router.post("/refresh")
async def refresh_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    next_auth_token = request.cookies.get("next-auth.session-token")
    new_access_token, new_refresh_token = auth_service.refresh_token_pair(next_auth_token, request)
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Tokens refreshed successfully"}
    )
    auth_service.set_auth_cookies(response, new_access_token, new_refresh_token)

    return response


@router.post("/logout")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    next_auth_token = request.cookies.get("next-auth.session-token")
    if not next_auth_token:
        raise SecurityException("No active session found")

    session_data = decode_next_auth_token(next_auth_token)

    refresh_token = session_data.get("refresh_token")
    if refresh_token:
        auth_service.revoke_token(refresh_token)

    access_token = session_data.get("access_token")
    if not access_token:
        raise SecurityException("No active access token found")
    auth_service.revoke_token(access_token)
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Logged out successfully"}
    )
    
    auth_service.clear_session(response)
    return response


@router.post("/signup")
async def signup(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.create_new_user(user_create)
    logger.info(f"New user {user.email} signed up successfully")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "User created successfully"}
    )
