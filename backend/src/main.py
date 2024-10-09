import asyncio
from backend.src.models.user import User
from db.session import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect

from api.auth import router as auth_router
from db.sync import sync_database
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

register_exception_handlers(app)

# Startup Event
@app.on_event("startup")
async def startup_event():
    await init_db()
    await sync_database()

# Routes
@app.get("/projects")
async def get_projects(
    current_user: User = Depends(get_current_user),
    api_key: APIKey = Depends(get_api_key)
):
    data_extractor = await DataExtractorFactory.create_data_extractor(api_key)
    projects = await data_extractor.get_all_projects()
    return projects

@app.get("/tickets/{project_key}")
async def get_tickets(
    project_key: str,
    current_user: User = Depends(get_current_user),
    api_key: APIKey = Depends(get_api_key)
):
    data_extractor = await DataExtractorFactory.create_data_extractor(api_key)
    tickets = await data_extractor.get_all_tickets(project_key)
    return tickets