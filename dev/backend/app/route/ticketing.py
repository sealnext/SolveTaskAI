from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agent.ticket_agent.graph import create_ticket_agent
from app.dependency import get_api_key_repository, get_project_service
from app.dto.status import StatusSchema
from app.repository.api_key import ApiKeyRepository
from app.service.project import ProjectService

router = APIRouter()


@router.get('/{project_id}/statuses', response_model=List[StatusSchema])
async def get_issue_statuses(
	project_id: int,
	request: Request,
	project_service: ProjectService = Depends(get_project_service),
	api_key_repository: ApiKeyRepository = Depends(get_api_key_repository),
):
	"""
	Get available statuses for a specific issue type in the project.
	Supports multiple ticketing systems (Jira, Azure DevOps, etc.)
	"""
	try:
		# Get project details
		project = await project_service.get_project_by_id(request.state.user.id, project_id)
		if not project:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'Project not found')

		# Get API key for the project
		api_key = await api_key_repository.get_by_project_id(project.id)
		if not api_key:
			raise HTTPException(status.HTTP_404_NOT_FOUND, 'API key not found for this project')

		# Get the appropriate ticketing client
		ticketing_client = await create_ticket_agent(api_key, project)

		if not ticketing_client:
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST,
				f'Unsupported ticketing system: {project.service_type}',
			)

		# Get statuses using the appropriate client
		# TODO PLEASE FIX THIS
		statuses = await ticketing_client.get_project_statuses()
		return statuses

	except Exception as e:
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
