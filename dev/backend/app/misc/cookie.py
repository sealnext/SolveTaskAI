from fastapi import Response

from app.misc.settings import settings


def set_session_cookie(response: Response, session_token: str) -> None:
	response.set_cookie(
		key='session_token',
		value=session_token,
		max_age=settings.session_ttl,
		secure=True,
		httponly=True,
		samesite='lax',
	)


def delete_session_cookie(response: Response) -> None:
	response.delete_cookie(key='session_token', secure=True, httponly=True, samesite='lax')
