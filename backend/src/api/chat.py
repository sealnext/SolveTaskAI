from fastapi import APIRouter, Depends
from dependencies import get_api_key_repository, get_project_service, get_chat_session_repository
from repositories import APIKeyRepository
from services.project_service import ProjectService
from services import Agent
from schemas import QuestionRequest, QuestionResponse
import logging
import uuid
from repositories.chat_session_repository import ChatSessionRepository

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=QuestionResponse)
async def chat(
    request: QuestionRequest,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
    chat_session_repository: ChatSessionRepository = Depends(get_chat_session_repository)
):
    logger.info(f"Chat request: {request}")
    
    project = await project_service.get_project_by_id(request.user_id, request.project_id)
    api_key = await api_key_repository.get_by_project_id(project.id)
    
    agent = Agent(project, api_key, chat_session_repository)
    
    # Create chat session if it doesn't exist
    if not request.chat_id:
        chat_session = await chat_session_repository.create(
            chat_id=f"chat_{uuid.uuid4()}",
            user_id=request.user_id,
            project_id=request.project_id
        )
        request.chat_id = chat_session.id
    
    answer, chat_id = await agent.process_question(request.question, request.chat_id)
    
    return QuestionResponse(answer=answer, chat_id=chat_id)