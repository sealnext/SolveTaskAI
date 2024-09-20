from fastapi import FastAPI
from data_extractor import DataExtractorFacade

app = FastAPI()


@app.get("/")
def read_root():
  return {"Hello": "World"}


@app.get("/projects")
def get_projects():
  return DataExtractorFacade.get_projects()
