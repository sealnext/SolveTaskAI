from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Tuple, Dict
import uuid
import logging

from utils.security import decode_next_auth_token

from config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    ENVIRONMENT
)
from exceptions.custom_exceptions import (
    InvalidTokenException,
    SecurityException
)

logger = logging.getLogger(__name__)

class AuthService:
    revoked_tokens: Dict[str, datetime] = {}

    def __init__(self):
        pass
    
    def revoke_session_tokens(self, session_data: dict) -> None:
        refresh_token = session_data.get("refresh_token")
        if refresh_token:
            self.revoke_token(refresh_token)

        access_token = session_data.get("access_token")
        if not access_token:
            raise SecurityException("No active access token found")
        self.revoke_token(access_token)

    def create_token_pair(self, email: str, request: Request) -> Tuple[str, str]:
        device_info, location = self._extract_request_localization(request)
        access_token = self._create_access_token(email, device_info, location)
        refresh_token = self._create_refresh_token(email, device_info, location)
        return access_token, refresh_token

    def _create_access_token(self, email: str, device_info: dict, location: str) -> str:
        try:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.now(timezone.utc) + expires_delta
            
            to_encode = {
                "sub": email,
                "exp": expire,
                "device": device_info,
                "location": location,
                "type": "access"
            }
            
            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            logger.error(f"Access token creation failed: {str(e)}")
            raise InvalidTokenException("Failed to create access token")

    def _create_refresh_token(self, email: str, device_info: dict, location: str) -> str:
        try:
            expires_delta = timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            expire = datetime.now(timezone.utc) + expires_delta
            
            to_encode = {
                "sub": email,
                "exp": expire,
                "device": device_info,
                "location": location,
                "type": "refresh",
                "jti": str(uuid.uuid4())
            }
            
            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            logger.error(f"Refresh token creation failed: {str(e)}")
            raise InvalidTokenException("Failed to create refresh token")

    @classmethod
    def verify_and_decode_token(cls, token: str, current_device_info: dict, current_location: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email: str = payload.get("sub")
            device_info: dict = payload.get("device")
            location: str = payload.get("location")
            token_type: str = payload.get("type")
            jti: str = payload.get("jti")

            if token_type == "refresh" and cls.is_token_revoked(jti):
                raise SecurityException("Token has been revoked")

            cls._check_device_compliance(device_info, current_device_info)
            cls._check_location(location, current_location)

            return email
        except JWTError:
            raise InvalidTokenException("Invalid token")

    def refresh_token_pair(self, next_auth_token: str, request: Request) -> Tuple[str, str]:
        session_data = self._decode_next_auth_token(next_auth_token)
        old_refresh_token = session_data.get("refresh_token")
        if not old_refresh_token:
            logger.info("Refresh token missing in session data")
            raise InvalidTokenException("Refresh token missing in session")

        try:
            payload = jwt.decode(old_refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "refresh":
                logger.info("Invalid token type detected")
                raise InvalidTokenException("Invalid token type")
            
            if payload.get("jti") in self.revoked_tokens:
                logger.info("Refresh token has been revoked")
                raise SecurityException("Refresh token has been revoked")
            
            email = payload.get("sub")
            self.revoke_token(old_refresh_token)
            return self.create_token_pair(email, request)

        except JWTError as e:
            logger.error(f"JWT decoding failed: {str(e)}")
            raise InvalidTokenException("Invalid refresh token")
        
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise InvalidTokenException("Failed to refresh tokens")

    def _decode_next_auth_token(self, next_auth_token: str) -> dict:
        if not next_auth_token:
            raise InvalidTokenException("Next-auth token missing")
        try:
            return decode_next_auth_token(next_auth_token)
        except Exception as e:
            logger.error(f"Failed to decode next-auth token: {str(e)}")
            raise InvalidTokenException("Invalid next-auth token")

    @classmethod
    def revoke_token(cls, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expiration = datetime.fromtimestamp(exp, tz=timezone.utc)
                cls.revoked_tokens[jti] = expiration
                cls._clean_expired_tokens()
        except JWTError:
            logger.warning("Failed to revoke token: Invalid token")
    
    @classmethod
    def is_token_revoked(cls, jti: str) -> bool:
        cls._clean_expired_tokens()
        return jti in cls.revoked_tokens

    @classmethod
    def _clean_expired_tokens(cls):
        current_time = datetime.now(timezone.utc)
        cls.revoked_tokens = {jti: exp for jti, exp in cls.revoked_tokens.items() if exp > current_time}

    @staticmethod
    def _check_device_compliance(stored_device_info: dict, current_device_info: dict):
        if stored_device_info != current_device_info:
            raise SecurityException("Unusual activity detected: Device mismatch")

    @staticmethod
    def _check_location(stored_location: str, current_location: str):
        if stored_location != current_location:
            raise SecurityException("Unusual activity detected: Location mismatch")

    @staticmethod
    def _extract_request_localization(request: Request):
        device_info = {
            "user_agent": request.headers.get("User-Agent"),
            "ip_address": request.client.host
        }
        location = request.headers.get("X-Forwarded-For", request.client.host)
        return device_info, location
    
    @staticmethod
    def clear_session(response: JSONResponse) -> None:
        response.delete_cookie(
            key="next-auth.session-token",
            secure=True,
            httponly=True,
            samesite="lax"
        )
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'