from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions.custom_exceptions import BaseCustomException


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(request: Request, exc: BaseCustomException):
        """Global handler for all custom exceptions. 
        This handler avoid us catching exceptions in every route.
        This handler will catch all the exceptions that inherit from BaseCustomException.

        1. Using the status_code defined in the exception
        2. Returning a JSON response with the exception's detail message
        
        This provides consistent error responses for all custom exceptions while
        allowing each exception to define its own status code and message.
        """
        return JSONResponse(
            status_code=exc.status_code, content={"message": exc.detail}
        )