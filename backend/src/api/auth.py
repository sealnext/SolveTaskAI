from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES

from schemas import UserCreate
from dependencies import get_auth_service, get_user_service

from services import UserService, AuthService

from exceptions import *

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    
    device_info = {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host
    }
    location = request.headers.get("X-Forwarded-For") or request.client.host
    
    access_token = auth_service.create_access_token_for_user(
        user.email,
        device_info=device_info,
        location=location
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Response(status_code=status.HTTP_200_OK)

@router.post("/signup")
async def signup(
    request: Request,
    response: Response,
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await user_service.create_new_user(user_create)
    
    device_info = {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host
    }
    location = request.headers.get("X-Forwarded-For") or request.client.host
    
    access_token = auth_service.create_access_token_for_user(
        user.email,
        device_info=device_info,
        location=location
    )

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Response(status_code=status.HTTP_200_OK)


async def get_current_user(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    token = response.cookies.get("access_token")
    if not token:
        raise InvalidTokenException
    
    token = token.replace("Bearer ", "")
    
    username = auth_service.verify_and_decode_token(token)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise UserNotFoundException
    return user
