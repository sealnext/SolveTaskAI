from fastapi import APIRouter, Request

from app.dependency import UserServiceDep
from app.dto.user import UserPublic

router = APIRouter()


@router.get('/profile')
async def get_user_profile(request: Request, user_service: UserServiceDep) -> UserPublic:
	user_id = request.state.user_id
	user_dto: UserPublic = await user_service.get_user_profile(user_id)
	return user_dto
