from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data_extractor import DataExtractorFacade

app = FastAPI()

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
