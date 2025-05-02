from asyncio import shield
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.misc.db_pool import langgraph_db_pool
from app.misc.exception import SessionNotFoundException
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
	await langgraph_db_pool.initialize()
	yield
	await langgraph_db_pool.close()
	await shield(async_db_engine.dispose())


app = FastAPI(lifespan=lifespan)


@app.middleware('http')
async def authorize(request: Request, call_next):
	if request.url.path.startswith('/api/auth') or request.url.path == '/api/health':
		return await call_next(request)

	session_token = request.cookies.get('session_token')
	if not session_token:
		return JSONResponse(
			status_code=status.HTTP_401_UNAUTHORIZED, content={'detail': 'Unauthorized'}
		)

	try:
		session_id: str = AuthService.get_session_id(session_token)
		user_id: str = await AuthService.get_user_id(session_id)
	except SessionNotFoundException:
		return JSONResponse(
			status_code=status.HTTP_401_UNAUTHORIZED, content={'detail': 'Unauthorized'}
		)
	except Exception as e:
		logger.error(f'Error retrieving user ID: {e}')
		return JSONResponse(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			content={'detail': 'Internal Server Error'},
		)

	request.state.session_id = session_id
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
