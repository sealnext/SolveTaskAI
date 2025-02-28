from config import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from api.projects import router as projects_router
from api.auth import router as auth_router
from api.apikey import router as api_keys_router
from api.chat import router as chat_router
from api.ticketing import router as ticketing_router
from api.agent import router as agent_router

from db import sync_database, init_db
from db.pool import db_pool
from exceptions.handlers import register_exception_handlers

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the lifecycle of our connection pool."""
    try:
        logger.info("Starting up SealNext API...")
        await init_db()
        await sync_database()
        async with db_pool:
            yield
    except Exception as e:
        logger.error(f"Error in connection pool lifecycle: {e}")
        raise

app = FastAPI(
    title="SealNext API",
    description="API for SealNext agent",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(agent_router)
app.include_router(ticketing_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(api_keys_router)
app.include_router(chat_router)

# Exception Handlers
register_exception_handlers(app)