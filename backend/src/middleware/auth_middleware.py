from fastapi import Request, Depends
from services import AuthService
from dependencies import get_auth_service
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.get_current_user(request)
    request.state.user = user
    return user
