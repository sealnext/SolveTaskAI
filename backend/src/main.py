import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect

from services import DataExtractorFacade
from api.auth import router as auth_router
from exceptions.handlers import register_exception_handlers
from db.sync import sync_database
from config import csrf_config

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await sync_database()

app.include_router(auth_router)

# Register custom exception handlers
register_exception_handlers(app)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSRF config
CsrfProtect.load_config(csrf_config)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/projects")
def get_projects():
    return DataExtractorFacade.get_projects()
