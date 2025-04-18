from asyncio import shield
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse

from app.misc.pool import db_pool
from app.misc.postgres import async_db_engine, init_db
from app.route.agent import router as agent_router
from app.route.apikey import router as api_keys_router
from app.route.auth import router as auth_router
from app.route.projects import router as projects_router
from app.route.ticketing import router as ticketing_router
from app.service.auth import AuthService

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
	await init_db()
	await db_pool.initialize()
	yield
	await db_pool.close()
	await shield(async_db_engine.dispose())


app = FastAPI(lifespan=lifespan)


@app.middleware('http')
async def authorize(request: Request, call_next):
	if request.url.path.startswith('/auth'):
		return await call_next(request)

	redirect_to_login = RedirectResponse('/auth/login')
	redirect_to_login.delete_cookie('session_token')

	session_token = request.cookies.get('session_token')
	if not session_token:
		return redirect_to_login

	user_id = await AuthService.get_user_id(session_token)
	if not user_id:
		return redirect_to_login

	request.state.user_id = user_id

	response = await call_next(request)
	return response


@app.get('/')
async def health():
	return {'status': 'ok'}


app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(ticketing_router)
app.include_router(projects_router)
app.include_router(api_keys_router)
