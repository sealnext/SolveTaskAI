# Standard library imports
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

# Third-party imports
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

# Local imports
from config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
)
from exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    SecurityException,
    UnexpectedErrorException,
    UserNotFoundException,
)
from models import User
from repositories import UserRepository
from utils.security import decode_next_auth_token, hash_password, verify_password

logger = logging.getLogger(__name__)

class AuthService:
    revoked_tokens: Dict[str, datetime] = {}

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def revoke_session_tokens(self, session_data: dict) -> None:
        refresh_token = session_data.get("refresh_token")
        if refresh_token:
            self.revoke_token(refresh_token)

        access_token = session_data.get("access_token")
        if not access_token:
            raise SecurityException("No active access token found")
        self.revoke_token(access_token)

    async def authenticate(self, password: str, user: User, request: Request) -> Tuple[str, str]:
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password")

        return self.create_token_pair(user.email, request)

    def create_token_pair(self, email: str, request: Request) -> Tuple[str, str]:
        location = self.extract_request_localization(request)
        access_token = self._create_access_token(email, location)
        refresh_token = self._create_refresh_token(email, location)
        return access_token, refresh_token

    def _create_access_token(self, email: str, location: str) -> str:
        try:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.now(timezone.utc) + expires_delta

            to_encode = {
                "sub": email,
                "exp": expire,
                "location": location,
                "type": "access"
            }

            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            logger.error(f"Access token creation failed: {str(e)}")
            raise InvalidTokenException("Failed to create access token")

    def _create_refresh_token(self, email: str, location: str) -> str:
        try:
            expires_delta = timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            expire = datetime.now(timezone.utc) + expires_delta

            to_encode = {
                "sub": email,
                "exp": expire,
                "location": location,
                "type": "refresh",
                "jti": str(uuid.uuid4())
            }

            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            logger.error(f"Refresh token creation failed: {str(e)}")
            raise InvalidTokenException("Failed to create refresh token")

    async def get_current_user(self, request: Request) -> User:
        next_auth_token = request.cookies.get("next-auth.session-token")
        if not next_auth_token:
            raise SecurityException("No active session found")

        try:
            location = self.extract_request_localization(request)
            session_data = self.verify_and_decode_token(next_auth_token, location)
            token = session_data.get("access_token")
            if not token:
                logger.info("Access token is missing in the session data")
                raise InvalidTokenException("Access token is missing")

            email = session_data.get("email")

            user = await self.user_repository.get_by_email(email)
            if user is None:
                logger.info(f"User with email {email} not found")
                raise UserNotFoundException("User not found")

            return user

        except (InvalidTokenException, UserNotFoundException, SecurityException) as e:
            logger.error(f"Authorization failed: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during authorization: {str(e)}")
            raise UnexpectedErrorException("An unexpected error occurred during authorization")

    def verify_and_decode_token(self, token: str, current_location: str) -> str:
        try:
            session_data = decode_next_auth_token(token)
            actual_token = session_data.get("access_token")

            if not actual_token:
                raise InvalidTokenException("Access token missing in session data")

            payload = jwt.decode(actual_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            location: str = payload.get("location")
            token_type: str = payload.get("type")
            jti: str = payload.get("jti")

            if token_type == "refresh" and self.is_token_revoked(jti):
                raise SecurityException("Token has been revoked")

            self._check_location(location, current_location)

            return session_data
        except JWTError as e:
            logger.error(f"JWT decoding failed: {str(e)}")
            raise InvalidTokenException("Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise InvalidTokenException("Failed to verify token")

    def refresh_token_pair(self, expired_refresh_token: str, request: Request) -> Tuple[str, str]:
        logger.info("Refreshing token pair")
        if not expired_refresh_token:
            logger.info("Refresh token missing in session data")
            raise InvalidTokenException("Refresh token missing in session")

        try:
            payload = jwt.decode(expired_refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            if payload.get("type") != "refresh":
                logger.info("Invalid token type detected")
                raise InvalidTokenException("Invalid token type")

            if payload.get("jti") in self.revoked_tokens:
                logger.info("Refresh token has been revoked")
                raise SecurityException("Refresh token has been revoked")

            email = payload.get("sub")
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
    def _check_location(stored_location: str, current_location: str):
        if stored_location != current_location:
            raise SecurityException("Unusual activity detected: Location mismatch")

    def extract_request_localization(self, request: Request):
        return request.headers.get("X-Forwarded-For", request.client.host)

    @staticmethod
    def clear_session(response: JSONResponse) -> None:
        response.delete_cookie(
            key="next-auth.session-token",
            secure=True,
            httponly=True,
            samesite="lax"
        )
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'

    async def change_password(self, email: str, old_password: str, new_password: str) -> None:
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundException("User not found")

        logger.info(f"Old password: {old_password}")
        logger.info(f"User hashed password: {user.hashed_password}")
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsException("Invalid old password")

        hashed_new_password = hash_password(new_password)
        await self.user_repository.update_password(user.id, hashed_new_password)
