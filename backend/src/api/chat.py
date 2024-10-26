from services.agent_service import perform_self_rag
from services.agent_service.rag.state import AgentState
from pydantic import BaseModel, Field
import logging
from fastapi import APIRouter
from services.project_service import ProjectService
from dependencies import get_api_key_repository, get_project_service
from repositories import APIKeyRepository
from fastapi import Depends

router = APIRouter(prefix="/chat")

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message")
    project_id: int = Field(..., description="The project ID")
    user_id: int = Field(..., description="The user ID")

@router.post("/")
async def chat(request: ChatRequest, 
                project_service: ProjectService = Depends(get_project_service),
                api_key_repository: APIKeyRepository = Depends(get_api_key_repository)
            ):
    logger.info(f"Chat request: {request}")
    
    project = await project_service.get_project_by_id(request.user_id, request.project_id)
    api_key = await api_key_repository.get_by_project_id(project.id)
    
    state = {
        "question": request.message,
        "project": project,
        "user_id": request.user_id,
        "documents": [],
        "max_retries": 1,
        "api_key": api_key,
        "status": "pending"
    }
    result = await perform_self_rag(state)
    logger.info(f"Chat result: {result}")
    return result