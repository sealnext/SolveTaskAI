from fastapi import APIRouter, Depends, Request, HTTPException
from middleware.auth_middleware import auth_middleware
from dependencies import get_api_key_repository, get_project_service, get_chat_session_repository
from repositories import APIKeyRepository
from services.project_service import ProjectService
from services import Agent
from schemas import QuestionRequest, QuestionResponse
import logging
import uuid
from repositories.chat_session_repository import ChatSessionRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(auth_middleware)]
)

@router.get("/{chat_id}")
async def get_chat_history(
    chat_id: str,
    request: Request,
    chat_session_repository: ChatSessionRepository = Depends(get_chat_session_repository)
):
    try:
        chat_session = await chat_session_repository.get_by_id(chat_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        if chat_session.user_id != request.state.user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        messages = await chat_session_repository.get_messages(chat_id)
        
        formatted_messages = []
        for msg in messages:
            if msg.get("type") == "system":
                continue
                
            formatted_message = {
                "role": "user" if msg.get("type") == "human" else "ai",
                "content": msg.get("content", "")
            }
            formatted_messages.append(formatted_message)
        
        return {"messages": formatted_messages}
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=QuestionResponse)
async def chat(
    question_request: QuestionRequest,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
    chat_session_repository: ChatSessionRepository = Depends(get_chat_session_repository)
):
    logger.info(f"Chat request: {question_request}")
    
    user_id = request.state.user.id
    project = await project_service.get_project_by_id(user_id, question_request.project_id)
    api_key = await api_key_repository.get_by_project_id(project.id)
    
    agent = Agent(project, api_key, chat_session_repository)
    
    if not question_request.chat_id:
        chat_session = await chat_session_repository.create(
            chat_id=f"chat_{uuid.uuid4()}",
            user_id=user_id,
            project_id=question_request.project_id
        )
        question_request.chat_id = chat_session.id
    
    answer, chat_id = await agent.process_question(question_request.question, question_request.chat_id)
    
    return QuestionResponse(answer=answer, chat_id=chat_id)