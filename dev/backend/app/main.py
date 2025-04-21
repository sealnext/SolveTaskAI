from asyncio import shield
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI

from app.misc.pool import db_pool
from app.misc.postgres import async_db_engine, init_db
from app.route.agent import router as agent_router
from app.route.apikey import router as api_keys_router
from app.route.auth import router as auth_router
from app.route.health import router as health_router
from app.route.projects import router as projects_router
from app.route.ticketing import router as ticketing_router

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
	await init_db()
	await db_pool.initialize()
	yield
	await db_pool.close()
	await shield(async_db_engine.dispose())


app = FastAPI(lifespan=lifespan)


app_router = APIRouter()

app_router.include_router(health_router, prefix='/health', tags=['Health'])
app_router.include_router(auth_router, prefix='/auth', tags=['Auth'])
app_router.include_router(agent_router, prefix='/agent', tags=['Agent'])
app_router.include_router(ticketing_router, prefix='/ticketing', tags=['Ticketing'])
app_router.include_router(projects_router, prefix='/projects', tags=['Projects'])
app_router.include_router(api_keys_router, prefix='/apikeys', tags=['API Keys'])

app.include_router(app_router, prefix='/api')
