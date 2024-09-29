from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .custom_exceptions import BaseCustomException
from fastapi_csrf_protect.exceptions import CsrfProtectError

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(request: Request, exc: BaseCustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
            "detail": "Invalid request data. Please check your input and try again.",
            "errors": exc.errors()
        }
    )

    @app.exception_handler(CsrfProtectError)
    async def csrf_protect_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.message})
