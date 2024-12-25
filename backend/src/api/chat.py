from fastapi import APIRouter, Depends, Request, HTTPException
from middleware.auth_middleware import auth_middleware
from dependencies import get_api_key_repository, get_project_service, get_chat_session_repository
from repositories import APIKeyRepository
from services.project_service import ProjectService

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

# TODO: extract the service logic to a separate file

@router.get("/{chat_id}")
async def get_chat_history(
    chat_id: str,
    request: Request,
    chat_session_repository: ChatSessionRepository = Depends(get_chat_session_repository)
):
    logger.info(f"Getting chat history for chat {chat_id}")
    try:
        chat_session = await chat_session_repository.get_by_id(chat_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        if chat_session.user_id != request.state.user.id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        messages = await chat_session_repository.get_messages(chat_id)
        
        return {
            "messages": messages,
            "project_id": chat_session.project_id
        }
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

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
    
    if question_request.chat_id:
        chat_session = await chat_session_repository.get_by_id(question_request.chat_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Resource not found")
            
        if chat_session.project_id != question_request.project_id:
            raise HTTPException(
                status_code=400, 
                detail="Invalid request parameters"
            )
        if chat_session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
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

@router.post("/history")
async def get_chat_history_list(
    request: Request,
    chat_session_repository: ChatSessionRepository = Depends(get_chat_session_repository)
):
    try:
        user_id = request.state.user.id
        
        logger.info(f"Getting chat sessions for user {user_id}")
        
        chat_sessions = await chat_session_repository.get_all_by_user_id(user_id)
        
        formatted_sessions = []
        for session in chat_sessions:
            message_count = sum(
                1 for msg in session.messages 
                if msg.get("role") in ["human", "ai"]
            ) if session.messages else 0
            
            formatted_session = {
                "id": session.id,
                "project_id": session.project_id,
                "created_at": session.updated_at.isoformat(),
                "preview": session.messages[0].get("content", "") if session.messages and len(session.messages) > 0 else "No messages",
                "message_count": message_count
            }
            formatted_sessions.append(formatted_session)
            
        return {"chat_sessions": formatted_sessions}
        
    except Exception as e:
        logger.error(f"Error retrieving chat history list: {str(e)}")
        return {"chat_sessions": []}