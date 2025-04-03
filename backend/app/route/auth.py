from hashlib import sha256
from logging import getLogger
from secrets import token_urlsafe
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl

from app.misc.settings import (
	AppSettings,
	GithubSettings,
	GoogleSettings,
	app_settings,
	github_settings,
	google_settings,
)

logger = getLogger(__name__)
router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login/google', response_class=RedirectResponse)
def login_google(
	app_settings: Annotated[AppSettings, Depends(app_settings)],
	oauth_settings: Annotated[GoogleSettings, Depends(google_settings)],
):
	GOOGLE_AUTH_URL: HttpUrl = 'https://accounts.google.com/o/oauth2/v2/auth'
	state = token_urlsafe(32)
	code_verifier = token_urlsafe(32)
	code_challenge = sha256(code_verifier.encode()).digest()

	params = {
		'client_id': oauth_settings.google_client_id,
		'redirect_uri': f'{app_settings.origin_url}/auth/callback/google',
		'response_type': 'code',
		'scope': 'openid email profile',
		'state': state,
		'code_verifier': code_verifier,
		'code_challenge_method': 'S256',
		'code_challenge': code_challenge,
	}

	auth_url = f'{GOOGLE_AUTH_URL}?{urlencode(params)}'
	return auth_url


@router.post('/callback/google')
def callback_google(
	app_settings: Annotated[AppSettings, Depends(app_settings)],
	oauth_settings: Annotated[GoogleSettings, Depends(google_settings)],
):
	pass


@router.post('/login/github', response_class=RedirectResponse)
def login_github(
	app_settings: Annotated[AppSettings, Depends(app_settings)],
	oauth_settings: Annotated[GithubSettings, Depends(github_settings)],
):
	pass


@router.post('/callback/github')
def callback_github(
	app_settings: Annotated[AppSettings, Depends(app_settings)],
	oauth_settings: Annotated[GithubSettings, Depends(github_settings)],
):
	pass
