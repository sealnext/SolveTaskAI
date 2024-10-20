from fastapi import status


class BaseCustomException(Exception):
    def __init__(self, detail: str, status_code: int):
        self.detail = detail
        self.status_code = status_code


class InvalidCredentialsException(BaseCustomException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class InvalidTokenException(BaseCustomException):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class SecurityException(BaseCustomException):
    def __init__(self, detail: str = "Authentication refused"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class UserAlreadyExistsException(BaseCustomException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)


class UserNotFoundException(BaseCustomException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class ValidationErrorException(BaseCustomException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail, status.HTTP_422_UNPROCESSABLE_ENTITY)


class UnexpectedErrorException(BaseCustomException):
    def __init__(self, detail: str = "An unexpected error occurred"):
        super().__init__(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class APIKeyNotFoundException(BaseCustomException):
    def __init__(self, detail: str = "No API keys found"):
        super().__init__({"message": "No API keys found", "data": []}, status.HTTP_200_OK)

class APIKeyExpiredException(BaseCustomException):
    def __init__(self, detail: str = "API Key has expired"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)

class APIKeyAlreadyExistsError(BaseCustomException):
    def __init__(self, detail: str = "An API key with this value already exists"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)
        
class ProjectNotFoundError(BaseCustomException):
    def __init__(self, detail: str = "Project not found"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)
        
class ProjectAlreadyExistsError(BaseCustomException):
    def __init__(self, detail: str = "Project already exists"):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)