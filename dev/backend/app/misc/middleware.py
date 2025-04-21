from fastapi import HTTPException, Request, status

from app.main import app
from app.misc.exception import SessionNotFoundException
from app.service.auth import AuthService


@app.middleware('http')
async def authorize(request: Request, call_next):
	if request.url.path.startswith('/api/auth') or request.url.path == '/api/health':
		return await call_next(request)

	session_token = request.cookies.get('session_token')
	if not session_token:
		return HTTPException(status.HTTP_401_UNAUTHORIZED, 'Unauthorized')

	try:
		user_id: int = await AuthService.get_user_id(session_token)
	except SessionNotFoundException:
		return HTTPException(status.HTTP_401_UNAUTHORIZED, 'Unauthorized')
	except Exception as e:
		raise e

	request.state.user_id = user_id

	response = await call_next(request)
	return response
