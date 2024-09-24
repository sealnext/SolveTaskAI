from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from schemas import Token, UserCreate
from dependencies import get_auth_service, get_user_service

from services import UserService, AuthService

from exceptions import *

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    access_token = auth_service.create_access_token_for_user(user.username)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signup", response_model=Token)
async def signup(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await user_service.create_new_user(user_create)
    access_token = auth_service.create_access_token_for_user(user.username)
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    username = auth_service.verify_and_decode_token(token)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise UserNotFoundException
    return user
