import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List

import httpx

from app.dto.api_key import ApiKey
from app.dto.project import ExternalProject, Project
from app.dto.ticket import JiraIssueSchema

logger = logging.getLogger(__name__)


class BaseTicketingClient(ABC):
	DEFAULT_TIMEOUT: int = 45

	def __init__(
		self,
		http_client: httpx.AsyncClient,
		api_key: ApiKey,
		project: Project | None = None,
	):
		self.http_client = http_client
		self.api_key = api_key
		self.project = project

	async def _make_request(
		self,
		method: str,
		url: str,
		timeout: float | None = None,
		**kwargs,
	) -> Dict[str, Any] | List[Any]:
		"""
		Makes an HTTP request, checks for HTTP errors, and returns parsed JSON.
		Any exception (connection, timeout, HTTP status, invalid JSON) is raised directly.

		Returns:
		    Dict[str, Any] | List[Any]: The parsed JSON response data.

		Raises:
		    httpx.HTTPStatusError: For 4xx/5xx responses.
		    httpx.RequestError: For connection errors, timeouts, etc.
		    json.JSONDecodeError: If the response is not valid JSON.
		    Exception: Any other unexpected error during the request.
		"""
		timeout = timeout or self.DEFAULT_TIMEOUT
		logger.debug(f'Making request: {method} {url}')

		response = await self.http_client.request(method, url, timeout=timeout, **kwargs)

		data = response.json()

		return data

	@abstractmethod
	async def get_projects(self) -> List[ExternalProject]:
		raise NotImplementedError

	@abstractmethod
	async def get_tickets(self) -> AsyncGenerator[JiraIssueSchema, None]:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket(self, ticket_id: str) -> JiraIssueSchema:
		raise NotImplementedError

	@abstractmethod
	async def delete_ticket(self, ticket_id: str, delete_subtasks: bool = False) -> str:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_edit_issue_metadata(self, ticket_id: str) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def search_user(self, query: str) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def find_sprint_by_name(self, sprint_name: str) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def search_issue_by_name(self, issue_name: str, max_results: int = 5) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_fields(self, ticket_id: str, fields: List[str]) -> Dict[str, Any]:
		raise NotImplementedError

	@abstractmethod
	async def update_ticket(
		self,
		ticket_id: str,
		payload: Dict[str, Any],
		notify_users: bool = False,
		transition_id: str | None = None,
	) -> None:
		raise NotImplementedError

	@abstractmethod
	async def revert_ticket_changes(
		self, ticket_id: str, version_number: int | None = None
	) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get_issue_createmeta(self, project_key: str, issue_type: str) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def create_ticket(self, payload: dict) -> dict:
		raise NotImplementedError

	@abstractmethod
	async def get_issue_types(self) -> List[Dict[str, Any]]:
		raise NotImplementedError
