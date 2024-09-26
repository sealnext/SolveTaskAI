from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from exceptions import InvalidTokenException

class AuthService:
    def create_access_token_for_user(self, email: str) -> str:
        try:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.now(timezone.utc) + expires_delta
            
            to_encode = {
                "sub": email,
                "exp": expire
            }
            
            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            raise InvalidTokenException(f"Token creation failed: {str(e)}")

    def verify_and_decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email: str = payload.get("sub")
            return email
        except JWTError:
            raise InvalidTokenException

