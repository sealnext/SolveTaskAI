from typing import List
from repositories import APIKeyRepository
from middleware.auth_middleware import auth_middleware
from fastapi import APIRouter, Depends, Request, HTTPException
from config.enums import TicketingSystemType
from dependencies import get_project_service, get_user_service, get_api_key_repository
from services import ProjectService, UserService
from schemas.status_schema import StatusSchema
from services.agent_service.ticketing_tool import create_ticketing_client

router = APIRouter(
    prefix="/ticketing",
    tags=["ticketing"],
    dependencies=[Depends(auth_middleware)]
)

@router.get("/{project_id}/statuses", response_model=List[StatusSchema])
async def get_issue_statuses(
    project_id: int,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository)
):
    """
    Get available statuses for a specific issue type in the project.
    Supports multiple ticketing systems (Jira, Azure DevOps, etc.)
    """
    try:
        # Get project details
        project = await project_service.get_project_by_id(request.state.user.id, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get API key for the project
        api_key = await api_key_repository.get_by_project_id(project.id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found for this project")

        # Get the appropriate ticketing client
        ticketing_client = await create_ticketing_client(api_key, project)
        
        if not ticketing_client:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported ticketing system: {project.service_type}"
            )

        # Get statuses using the appropriate client
        statuses = await ticketing_client.get_project_statuses()
        return statuses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 