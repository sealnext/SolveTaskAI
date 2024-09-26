from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from exceptions import InvalidTokenException, SecurityException

class AuthService:
    def create_access_token_for_user(self, email: str, device_info: dict, location: str) -> str:
        try:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.now(timezone.utc) + expires_delta
            
            to_encode = {
                "sub": email,
                "exp": expire,
                "device": device_info,
                "location": location
            }
            
            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            raise InvalidTokenException(f"Token creation failed: {str(e)}")

    def verify_and_decode_token(self, token: str, current_device_info: dict, current_location: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email: str = payload.get("sub")
            device_info: dict = payload.get("device")
            location: str = payload.get("location")

            self._check_device_compliance(device_info, current_device_info)
            self._check_location(location, current_location)

            return email
        except JWTError:
            raise InvalidTokenException

    def _check_device_compliance(self, stored_device_info: dict, current_device_info: dict):
        if stored_device_info != current_device_info:
            raise SecurityException("Device mismatch detected")

    def _check_location(self, stored_location: str, current_location: str):
        if stored_location != current_location:
            raise SecurityException("Unusual location detected")

