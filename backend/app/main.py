from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logging import getLogger

from app.api.projects import router as projects_router
from app.api.apikey import router as api_keys_router
from app.api.chat import router as chat_router
from app.api.ticketing import router as ticketing_router
from app.api.agent import router as agent_router

from app.db.postgres import init_db
from app.db.postgres import engine
from app.exceptions.handlers import register_exception_handlers

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health():
    return {"status": "ok"}


# Routers
app.include_router(agent_router)
app.include_router(ticketing_router)
app.include_router(projects_router)
app.include_router(api_keys_router)
app.include_router(chat_router)

# Exception Handlers
register_exception_handlers(app)
