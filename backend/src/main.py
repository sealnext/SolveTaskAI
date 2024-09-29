import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect

from api.auth import router as auth_router
from config import csrf_config
from db.sync import sync_database
from exceptions.handlers import register_exception_handlers
from services import DataExtractorFacade

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CsrfProtect.load_config(csrf_config)

# Routers
app.include_router(auth_router)

register_exception_handlers(app)

# Startup Event
@app.on_event("startup")
async def startup_event():
    await sync_database()

# Routes
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/projects")
def get_projects():
    return DataExtractorFacade.get_projects()
