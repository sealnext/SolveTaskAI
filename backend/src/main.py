from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect

from api.projects import router as projects_router
from api.auth import router as auth_router
from api.apikey import router as api_keys_router

from db import sync_database, init_db
from exceptions.handlers import register_exception_handlers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(api_keys_router)

# Exception Handlers
register_exception_handlers(app)

# Startup Event
@app.on_event("startup")
async def startup_event():
    await init_db()
    await sync_database()
