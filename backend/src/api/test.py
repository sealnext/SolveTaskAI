from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List
from dependencies import get_project_repository, get_api_key_repository
from repositories import ProjectRepository, APIKeyRepository
from services.data_extractor.data_extractor_factory import create_data_extractor
from services.agent_service import process_documents
from schemas import Ticket

import logging

logger = logging.getLogger(__name__)

# THIS FILE IS JUST FOR TESTING PURPOSES

router = APIRouter()


@router.post("/process_documents")
async def process_documents_endpoint(
    project_repository: ProjectRepository = Depends(get_project_repository),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository)
):
    user_id = 1
    project_id = 47
    project = await project_repository.get_by_id(user_id, project_id)
    api_key = await api_key_repository.get_by_project_id(project.id)
    
    initial_state = {
        "question": "",
        "project": project,
        "api_key": api_key,
        "user_id": user_id,
        "generation": "",
        "max_retries": 3,
        "answers": 0,
        "loop_step": 0,
        "documents": [],
        "tickets": []
    }
    
    final_state = await process_documents(
        initial_state
    )
    
    return {
        "answer": final_state["generation"],
        "documents": final_state["documents"],
        "tickets": final_state["tickets"]
    }
