from asyncio import shield
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request, status

from app.misc.exception import SessionNotFoundException
from app.misc.pool import db_pool
from app.misc.postgres import async_db_engine, init_db
from app.route.agent import router as agent_router
from app.route.apikey import router as api_keys_router
from app.route.auth import router as auth_router
from app.route.health import router as health_router
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


app_router = APIRouter()

app_router.include_router(health_router, prefix='/health', tags=['Health'])
app_router.include_router(auth_router, prefix='/auth', tags=['Auth'])
app_router.include_router(agent_router, prefix='/agent', tags=['Agent'])
app_router.include_router(ticketing_router, prefix='/ticketing', tags=['Ticketing'])
app_router.include_router(projects_router, prefix='/projects', tags=['Projects'])
app_router.include_router(api_keys_router, prefix='/apikeys', tags=['API Keys'])

app.include_router(app_router, prefix='/api')
