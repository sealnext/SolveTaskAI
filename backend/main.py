from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.data_extractor import DataExtractorFacade
from api.auth import router as auth_router
from exceptions.handlers import register_exception_handlers

app = FastAPI()

# Register the auth router
app.include_router(auth_router)

# Register custom exception handlers
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
  return {"Hello": "World"}


@app.get("/projects")
def get_projects():
  return DataExtractorFacade.get_projects()
