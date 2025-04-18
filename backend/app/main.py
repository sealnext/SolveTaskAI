from asyncio import shield
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.misc.pool import db_pool
from app.misc.postgres import async_db_engine, init_db
from app.route.agent import router as agent_router
from app.route.apikey import router as api_keys_router
from app.route.auth import router as auth_router
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

app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


@app.get('/')
async def health():
	return {'status': 'ok'}


app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(ticketing_router)
app.include_router(projects_router)
app.include_router(api_keys_router)
