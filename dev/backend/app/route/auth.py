from urllib.parse import urljoin

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.dependency import AuthServiceDep
from app.dto.user import UserCreateByPassword, UserLogin
from app.misc.cookie import delete_session_cookie, set_session_cookie
from app.misc.exception import TokenNotFoundException
from app.misc.logger import logger
from app.misc.settings import settings

router = APIRouter()


@router.get('/verify')
async def verify_user_session():
	# Route to verify if the user is authenticated
	# *** This doesn't bypass the middleware (special case) ***
	return Response()


@router.post('/login')
async def login(auth_service: AuthServiceDep, user_dto: UserLogin):
	try:
		session_token: str = await auth_service.login(user_dto)
	except Exception as e:
		logger.exception(f'Log in failed: {e}')
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Log in failed')

	response = Response()  # http status 200
	set_session_cookie(response, session_token)

	return response


@router.post('/logout')
async def logout(auth_service: AuthServiceDep, request: Request):
	try:
		await auth_service.logout(request.state.session_id)
	except Exception as e:
		logger.exception(f'Log out failed: {e}')
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Log out failed')

	response = Response()  # http status 200
	delete_session_cookie(response)

	return response


@router.post('/signup')
async def signup(
	auth_service: AuthServiceDep, user_dto: UserCreateByPassword, background_tasks: BackgroundTasks
):
	try:
		session_token: str = await auth_service.register(user_dto, background_tasks)
	except Exception as e:
		logger.exception(f'Sign up failed: {e}')
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Sign up failed')

	response = Response(status_code=status.HTTP_201_CREATED)
	set_session_cookie(response, session_token)

	return response


@router.get('/verify-email')
async def verify_email(auth_service: AuthServiceDep, token: str):
	try:
		await auth_service.verify_email(token)

	except TokenNotFoundException as e:
		logger.error(f'Token not found: {e}')
		raise HTTPException(status.HTTP_404_NOT_FOUND, 'Token not found')

	except Exception as e:
		logger.exception(f'Email verification failed: {e}')
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Email verification failed')

	login_url: str = urljoin(str(settings.origin_url), '/login?email_verified=true')
	return RedirectResponse(login_url)


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
