from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Tuple, Dict
import uuid

from config import (
    CSRF_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
)
from exceptions import InvalidTokenException, SecurityException

class AuthService:
    def __init__(self):
        self.revoked_tokens: Dict[str, datetime] = {}

    # Token creation and management
    def create_token_pair(self, email: str, device_info: dict, location: str) -> Tuple[str, str]:
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
            raise InvalidTokenException(f"Access token creation failed: {str(e)}")

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
            raise InvalidTokenException(f"Refresh token creation failed: {str(e)}")

    # Token verification and refresh
    @staticmethod
    def verify_and_decode_token(token: str, current_device_info: dict, current_location: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email: str = payload.get("sub")
            device_info: dict = payload.get("device")
            location: str = payload.get("location")
            token_type: str = payload.get("type")
            jti: str = payload.get("jti")

            if token_type == "refresh" and AuthService.is_token_revoked(jti):
                raise SecurityException("Token has been revoked")

            AuthService._check_device_compliance(device_info, current_device_info)
            AuthService._check_location(location, current_location)

            return email
        except JWTError:
            raise InvalidTokenException

    def refresh_token_pair(self, refresh_token: str, device_info: dict, location: str) -> Tuple[str, str]:
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                raise InvalidTokenException("Invalid token type")
            
            if payload.get("jti") in self.revoked_tokens:
                raise SecurityException("Refresh token has been revoked")
            
            email = payload.get("sub")
            self._check_device_compliance(payload.get("device"), device_info)
            self._check_location(payload.get("location"), location)
            
            self.revoke_token(refresh_token)
            
            return self.create_token_pair(email, device_info, location)
        except JWTError:
            raise InvalidTokenException

    # Token revocation
    def revoke_token(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expiration = datetime.fromtimestamp(exp, tz=timezone.utc)
                self.revoked_tokens[jti] = expiration
                self._clean_expired_tokens()
        except JWTError:
            pass

    def is_token_revoked(self, jti: str) -> bool:
        self._clean_expired_tokens()
        return jti in self.revoked_tokens

    def _clean_expired_tokens(self):
        current_time = datetime.now(timezone.utc)
        self.revoked_tokens = {jti: exp for jti, exp in self.revoked_tokens.items() if exp > current_time}

    # Security checks
    @staticmethod
    def _check_device_compliance(stored_device_info: dict, current_device_info: dict):
        if stored_device_info != current_device_info:
            raise SecurityException("Unusual activity")

    @staticmethod
    def _check_location(stored_location: str, current_location: str):
        if stored_location != current_location:
            raise SecurityException("Unusual activity")

    # Request and response handling
    @staticmethod
    def extract_request_localization(request: Request):
        device_info = {
            "user_agent": request.headers.get("User-Agent"),
            "ip_address": request.client.host
        }
        location = request.headers.get("X-Forwarded-For", request.client.host)
        return device_info, location
    
    # Clear session from cookies and headers
    @staticmethod
    def clear_session(response: JSONResponse) -> None:
        response.delete_cookie(
            key="next-auth.session-token",
            secure=True,
            httponly=True,
            samesite="lax"
            )
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'