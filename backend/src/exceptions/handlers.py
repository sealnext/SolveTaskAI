from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_csrf_protect.exceptions import CsrfProtectError
from .custom_exceptions import BaseCustomException
from fastapi import HTTPException
from .custom_exceptions import NotImplementedException

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(request: Request, exc: BaseCustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail}
        )

    @app.exception_handler(NotImplementedError)
    async def not_implemented_exception_handler(request: Request, exc: NotImplementedError):
        return NotImplementedException()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Invalid request data. Please check your input and try again.",
                "errors": exc.errors()
            }
        )

    @app.exception_handler(CsrfProtectError)
    async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"}
        )