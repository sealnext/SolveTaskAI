from logging import getLogger

from fastapi import APIRouter, Response
from starlette.responses import RedirectResponse

from app.dependency import AuthServiceDep
from app.dto.user import UserCreateByPassword, UserLogin
from app.misc.settings import settings

logger = getLogger(__name__)
router = APIRouter(prefix='/auth', tags=['auth'])


def _set_session_cookie(response: Response, session_token: str) -> None:
	response.set_cookie(
		key='session_token',
		value=session_token,
		max_age=settings.session_ttl,
		secure=True,
		httponly=True,
		samesite='lax',
	)


@router.post('/login')
async def login(
	auth_service: AuthServiceDep,
	user_dto: UserLogin,
	response: Response,
):
	session_token: str = await auth_service.login(user_dto)
	_set_session_cookie(response, session_token)
	return RedirectResponse('/')


@router.post('/signup')
async def signup(
	auth_service: AuthServiceDep,
	user_dto: UserCreateByPassword,
	response: Response,
):
	session_token: str = await auth_service.register(user_dto)
	_set_session_cookie(response, session_token)
	return RedirectResponse('/')


# @router.post('/login/google', response_class=RedirectResponse)
# def login_google():
# 	state = token_urlsafe(32)
# 	code_verifier = token_urlsafe(32)
# 	code_challenge = sha256(code_verifier.encode()).digest()
#
# 	params = {
# 		'client_id': oauth_settings.google_client_id,
# 		'redirect_uri': f'{app_settings.origin_url}/auth/callback/google',
# 		'response_type': 'code',
# 		'scope': 'openid email profile',
# 		'state': state,
# 		'code_verifier': code_verifier,
# 		'code_challenge_method': 'S256',
# 		'code_challenge': code_challenge,
# 	}
#
# 	auth_url = f'{oauth_settings.auth_url}?{urlencode(params)}'
# 	return auth_url
#
#
# @router.post('/callback/google')
# def callback_google():
# 	pass
#
#
# @router.post('/login/github', response_class=RedirectResponse)
# def login_github():
# 	pass
#
#
# @router.post('/callback/github')
# def callback_github():
# 	pass
