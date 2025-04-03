from typing import AsyncGenerator, List

from app.schema.api_key import APIKey
from app.schema.project import ExternalProject
from app.schema.ticket import JiraIssueSchema
from app.service.ticketing.client import BaseTicketingClient


class AzureClient(BaseTicketingClient):
	"""Azure DevOps-specific implementation of the ticketing client."""

	async def get_projects(self) -> List[ExternalProject]:
		headers = self._get_auth_headers(self.api_key)
		url = f'https://dev.azure.com/{self.api_key.organization}/_apis/projects'
		data = await self._make_request('GET', url, headers=headers)
		return [ExternalProject(**project) for project in data['value']]

	async def get_tickets(self) -> AsyncGenerator[JiraIssueSchema, None]:
		# TODO: Implement Azure-specific ticket fetching
		raise NotImplementedError('Azure ticket fetching not implemented yet')

	def _get_auth_headers(self, api_key: APIKey) -> dict:
		return {
			'Authorization': f'Bearer {api_key.api_key}',
			'Accept': 'application/json',
		}
