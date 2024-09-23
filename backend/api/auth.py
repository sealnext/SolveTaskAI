from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from jose import JWTError, jwt
from datetime import timedelta
from pydantic import ValidationError

from schemas import Token, UserCreate
from models import User

from services.user_service import UserService
from services.auth_service import AuthService

from exceptions import *

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Singleton for AuthService
auth_service_instance = AuthService()

def get_auth_service():
    return auth_service_instance

# New instance for UserService (likely stateful?, interacting with DB)
def get_user_service():
    return UserService()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise InvalidCredentialsException
    
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signup", response_model=Token)
async def signup(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        existing_user = await user_service.get_user_by_username(user_create.username)
        if existing_user:
            raise UserAlreadyExistsException
        
        user = await user_service.create_user(user_create)
        access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    except ValidationError as e:
        raise ValidationErrorException(f"Validation error: {e.errors()}")


# Dependency to get the current user based on JWT token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        
    except JWTError:
        raise InvalidTokenException

    user = await user_service.get_user_by_username(username)
    if user is None:
        raise UserNotFoundException
    return user
