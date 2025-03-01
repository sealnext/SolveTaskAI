from typing import List
from app.repositories.apikey_repository import APIKeyRepository
from app.middleware.auth_middleware import auth_middleware
from fastapi import APIRouter, Depends, Request, HTTPException
from app.dependencies import get_project_service, get_api_key_repository
from app.services.project_service import ProjectService
from app.schemas.status import StatusSchema
from app.agent.ticket_agent.graph import create_ticket_agent

router = APIRouter(
    prefix="/ticketing", tags=["ticketing"], dependencies=[Depends(auth_middleware)]
)


@router.get("/{project_id}/statuses", response_model=List[StatusSchema])
async def get_issue_statuses(
    project_id: int,
    request: Request,
    project_service: ProjectService = Depends(get_project_service),
    api_key_repository: APIKeyRepository = Depends(get_api_key_repository),
):
    """
    Get available statuses for a specific issue type in the project.
    Supports multiple ticketing systems (Jira, Azure DevOps, etc.)
    """
    try:
        # Get project details
        project = await project_service.get_project_by_id(
            request.state.user.id, project_id
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get API key for the project
        api_key = await api_key_repository.get_by_project_id(project.id)
        if not api_key:
            raise HTTPException(
                status_code=404, detail="API key not found for this project"
            )

        # Get the appropriate ticketing client
        ticketing_client = await create_ticket_agent(api_key, project)

        if not ticketing_client:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported ticketing system: {project.service_type}",
            )

        # Get statuses using the appropriate client
        # TODO PLEASE FIX THIS
        statuses = await ticketing_client.get_project_statuses()
        return statuses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
