import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dependencies import get_auth_service, get_user_service
from exceptions import *
from services import AuthService, UserService
from validation_models import UserCreate
from utils.cookie_manager import set_auth_cookies
from utils.security import decode_next_auth_token

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
    user = await user_service.get_user_by_email(form_data.username)
    
    access_token, refresh_token = await auth_service.authenticate(
        form_data.password, user, request
    )
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Login successful",
                 "full_name": user.full_name}
    )
    set_auth_cookies(response, access_token, refresh_token)

    return response


@router.post("/refresh")
async def refresh_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    expired_refresh_token = request.cookies.get("refresh-token")
    new_access_token, new_refresh_token = auth_service.refresh_token_pair(expired_refresh_token, request)
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Tokens refreshed successfully"}
    )
    set_auth_cookies(response, new_access_token, new_refresh_token)

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
    
    auth_service.revoke_session_tokens(session_data)
    
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
