from fastapi import APIRouter, Depends, Response, Request, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from datetime import timedelta
from config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS, CSRF_TOKEN_EXPIRE_MINUTES, NEXTAUTH_SECRET
from fastapi_csrf_protect import CsrfProtect

from validation_models import UserCreate
from dependencies import get_auth_service, get_user_service

from services import UserService, AuthService
from utils.security import decode_next_auth_token

from exceptions import *

import logging

logger = logging.getLogger(__name__)

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
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        
        device_info, location = auth_service.extract_request_localization(request)
        
        access_token, refresh_token = auth_service.create_token_pair(
            user.email,
            device_info=device_info,
            location=location
        )
        
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        set_auth_cookies(response, access_token, refresh_token, csrf_protect, signed_token)
        
        logger.info(f"User {user.email} logged in successfully")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={ # TODO: REMOVE RETURNING TOKENS IN CONTENT
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "csrf_token": csrf_token
            }
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed authentication")

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    csrf_protect: CsrfProtect = Depends(),
):
    next_auth_token = request.cookies.get("next-auth.session-token")
    if not next_auth_token:
        raise InvalidTokenException("Next-auth token missing")
    
    session_data = decode_next_auth_token(next_auth_token)
    csrf_protect.validate_csrf(session_data.get("csrf_token"))
    old_refresh_token = session_data.get("refresh_token")
    if not old_refresh_token:
        raise InvalidTokenException("Refresh token missing")
    
    device_info = {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host
    }
    location = request.headers.get("X-Forwarded-For", request.client.host)
    
    new_access_token, new_refresh_token, access_token_expiry = auth_service.refresh_token_pair(
        old_refresh_token,
        device_info=device_info,
        location=location
    )
    
    if not new_access_token or not new_refresh_token:
        raise InvalidTokenException("Failed to generate new tokens")

    auth_service.revoke_refresh_token(old_refresh_token)
    
    new_session_data = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "csrf_token": session_data["csrf_token"]
    }
    
    new_next_auth_token = jwt.encode({"sub": json.dumps(new_session_data)}, NEXTAUTH_SECRET, algorithm="HS256")
    
    response.set_cookie(
        key="next-auth.session-token",
        value=new_next_auth_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={
            "message": "Tokens refreshed successfully",
            "access_token_expiry": access_token_expiry.isoformat()
        }
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        next_auth_token = request.cookies.get("next-auth.session-token")
        if next_auth_token:
            session_data = decode_next_auth_token(next_auth_token)
            csrf_protect.validate_csrf(session_data.get("csrf_token"))
            refresh_token = session_data.get("refresh_token")
            if refresh_token:
                auth_service.revoke_refresh_token(refresh_token)
        
        response.delete_cookie("next-auth.session-token")
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
        
        logger.info("User logged out successfully")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Logged out successfully"})
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed")

async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        next_auth_token = request.cookies.get("next-auth.session-token")
        if not next_auth_token:
            raise InvalidTokenException("Next-auth token is missing")
        
        session_data = decode_next_auth_token(next_auth_token)
        csrf_protect.validate_csrf(session_data.get("csrf_token"))
        token = session_data.get("access_token")
        if not token:
            raise InvalidTokenException("Access token is missing")
        
        device_info, location = auth_service.extract_request_localization(request)
        
        username = auth_service.verify_and_decode_token(token, device_info, location)
        user = await user_service.get_user_by_username(username)
        if user is None:
            raise UserNotFoundException
        return user
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed authorization")

@router.post("/signup")
async def signup(
    request: Request,
    response: Response,
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        user = await user_service.create_new_user(user_create)
        
        device_info, location = auth_service.extract_request_localization(request)
        
        access_token, refresh_token = auth_service.create_token_pair(
            user.email,
            device_info=device_info,
            location=location
        )

        set_auth_cookies(response, access_token, refresh_token, csrf_protect)
        
        logger.info(f"New user {user.email} signed up successfully")
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "User created successfully"})
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signup failed")
    
def set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_protect: CsrfProtect, signed_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    response.set_cookie(
        key="csrf_token",
        value=signed_token,
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=timedelta(minutes=CSRF_TOKEN_EXPIRE_MINUTES)
    )
