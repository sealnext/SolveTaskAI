import asyncio
import base64
import re
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Union
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException, status

from app.dto.api_key import ApiKey
from app.dto.project import ExternalProject, Project
from app.dto.ticket import JiraIssueContentSchema, JiraIssueSchema
from app.misc.logger import logger
from app.misc.settings import settings
from app.service.ticketing.client import BaseTicketingClient


class TicketingSystemType(str, Enum):
	JIRA = 'jira'
	AZURE = 'azure'


class JiraClient(BaseTicketingClient):
	"""Jira-specific implementation of the ticketing client."""

	BATCH_SIZE = settings.jira_max_results_per_page
	API_VERSION = settings.jira_api_version

	def __init__(
		self,
		http_client: httpx.AsyncClient,
		api_key: ApiKey,
		project: Project | None = None,
	):
		super().__init__(http_client, api_key, project)
		self._base_urls: Dict[str, httpx.URL] = {}

	def _get_base_url(self) -> httpx.URL:
		"""Get or create base URL for the API."""
		if self.api_key.domain not in self._base_urls:
			self._base_urls[self.api_key.domain] = httpx.URL(self.api_key.domain)
		return self._base_urls[self.api_key.domain]

	def _build_url(self, *path_segments: str) -> str:
		"""Build URL by joining path segments correctly."""
		base_url = self._get_base_url()
		# Ensure base URL ends with a slash if it doesn't have one
		base_url_str = str(base_url)
		if not base_url_str.endswith('/'):
			base_url_str += '/'

		# Construct the relative path
		relative_path = (
			'rest/api/'
			+ str(self.API_VERSION)
			+ '/'
			+ '/'.join(str(segment).strip('/') for segment in path_segments)
		)
		# Use urljoin for robust path joining
		return urljoin(base_url_str, relative_path)

	def _validate_project_key(self, project_key: str) -> None:
		"""Validate project key format."""
		if not project_key or not isinstance(project_key, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid project key')

	def _get_auth_headers(self) -> dict:
		"""Get authentication headers for Jira API."""
		auth_str = f'{self.api_key.domain_email}:{self.api_key.api_key}'
		auth_bytes = auth_str.encode('ascii')
		base64_auth = base64.b64encode(auth_bytes).decode('ascii')
		return {'Authorization': f'Basic {base64_auth}', 'Accept': 'application/json'}

	async def get_projects(self) -> List[ExternalProject]:
		"""Get all projects accessible by the API key with efficient pagination."""
		url = self._build_url('project')
		all_projects = []
		start_at = 0

		while True:
			params = {'startAt': start_at, 'maxResults': self.BATCH_SIZE}

			try:
				logger.info('Fetching projects from %s with params %s', url, params)
				data = await self._make_request(
					'GET', url, headers=self._get_auth_headers(), params=params
				)

				# Jira Cloud returns a list directly
				if isinstance(data, list):
					projects = [ExternalProject.model_validate(project) for project in data]
					logger.info('Processing response as Jira Cloud list format')
				# Jira Server returns an object with 'values'
				elif isinstance(data, dict) and 'values' in data:
					projects = [
						ExternalProject.model_validate(project)
						for project in data.get('values', [])
					]
					logger.info('Processing response as Jira Server object format')
				else:
					# Handle unexpected format
					logger.warning('Unexpected project response format: %s', type(data))
					projects = []

				if not projects and start_at == 0 and not all_projects:
					# If first request returns empty and no projects found yet, maybe no permissions
					logger.warning('Initial project fetch returned empty list. Check permissions.')
					# We might break here or continue depending on desired behavior for empty lists
					# break

				all_projects.extend(projects)
				logger.info('Fetched %s projects in this batch.', len(projects))

				# Determine if this is the last page
				is_last = False
				if isinstance(data, list):
					# Cloud: Assume last page if fewer items than maxResults requested
					if len(projects) < self.BATCH_SIZE:
						is_last = True
				elif isinstance(data, dict):
					# Server: Check 'isLast' field if available, otherwise use count
					if data.get('isLast', False) or len(projects) < self.BATCH_SIZE:
						is_last = True

				if is_last:
					logger.info('Detected last page of projects.')
					break

				start_at += len(projects)  # More robust pagination using actual count

			except httpx.HTTPStatusError as e:
				if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
					logger.error(
						'Authentication failed when fetching projects. Check API key and email.'
					)
					raise HTTPException(
						status.HTTP_401_UNAUTHORIZED,
						'Jira authentication failed. Check API key and email.',
					)

				if e.response.status_code == status.HTTP_403_FORBIDDEN:
					logger.error(
						'Permission denied when fetching projects. Check API key permissions.'
					)
					raise HTTPException(
						status.HTTP_403_FORBIDDEN,
						'Jira permission denied. The API key may lack project browsing permissions.',
					)

				logger.exception(
					'HTTP error fetching projects: %s - %s', e.response.status_code, e.response.text
				)
				raise HTTPException(
					e.response.status_code,
					'Failed to fetch projects: %s',
					e.response.text,
				)
			except Exception as e:
				logger.error('Unexpected error fetching projects: %s', e, exc_info=True)
				raise HTTPException(
					status.HTTP_500_INTERNAL_SERVER_ERROR,
					'Failed to fetch projects due to an unexpected error: %s',
					e,
				)

		if not all_projects:
			logger.warning('No projects found in Jira for the provided API key.')
			# Consider if 404 is appropriate or just return empty list
			# raise HTTPException(
			#     status.HTTP_404_NOT_FOUND,
			#     "No projects found in Jira. Please check your API key and permissions.",
			# )

		return all_projects

	async def _fetch_tickets_batch(self, start_at: int) -> List[JiraIssueSchema]:
		"""Fetch a batch of tickets for the client's project."""
		if not self.project or not self.project.key:
			raise ValueError(
				'Project context is required for fetching tickets but was not provided '
				'during client initialization.'
			)

		params = {
			'jql': f'project = {self.project.key}',
			'maxResults': self.BATCH_SIZE,  # Use BATCH_SIZE here
			'startAt': start_at,
			'fields': (
				'summary,description,customfield_10008,comment,status,'
				'priority,issuetype,labels,resolution,parent,'
				'assignee,reporter,resolutiondate,created,updated,project'
			),
		}

		try:
			response_data = await self._make_request(
				'GET',
				self._build_url('search'),
				headers=self._get_auth_headers(),
				params=params,
			)
			# Ensure response_data is treated as a dictionary
			issues = response_data.get('issues', []) if isinstance(response_data, dict) else []

			validated_issues = []
			for issue in issues:
				try:
					# Add project_id manually if needed, extracting from fields
					project_data = issue.get('fields', {}).get('project', {})
					project_id = str(project_data.get('id')) if project_data else None
					validated_issues.append(
						JiraIssueSchema.model_validate({**issue, 'project_id': project_id})
					)
				except Exception as val_err:
					logger.warning(
						'Skipping issue due to validation error: %s. Issue data: %s', val_err, issue
					)

			return validated_issues

		except Exception as e:
			logger.error(
				'Error fetching tickets batch at %s for project %s: %s',
				start_at,
				self.project.key,
				e,
			)
			# Re-raise the exception to be handled by the caller (get_tickets)
			raise

	async def get_tickets(self) -> AsyncGenerator[JiraIssueSchema, None]:
		"""Get all tickets for the client's project with efficient batch processing."""
		if not self.project or not self.project.key:
			raise ValueError(
				'Project context is required for getting tickets but was not provided '
				'during client initialization.'
			)

		url = self._build_url('search')
		project_key = self.project.key
		logger.info('Starting to fetch tickets for project: %s', project_key)

		# First, get total number of tickets
		try:
			params_total = {
				'jql': f'project = {project_key}',
				'maxResults': 0,
			}
			data_total = await self._make_request(
				'GET',
				url,
				headers=self._get_auth_headers(),
				params=params_total,
			)
			total_tickets = data_total.get('total', 0) if isinstance(data_total, dict) else 0
			logger.info('Total tickets found for project %s: %s', project_key, total_tickets)

		except Exception as e:
			logger.error('Failed to get total ticket count for project %s: %s', project_key, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR, 'Failed to get ticket count: %s', e
			)

		if total_tickets == 0:
			logger.info('No tickets found for project %s. Exiting.', project_key)
			return  # Return empty generator

		# Process in batches using concurrent requests
		semaphore = asyncio.Semaphore(settings.jira_max_concurrent_requests)
		tasks = []

		for start_at in range(0, total_tickets, self.BATCH_SIZE):

			async def fetch_with_semaphore(s_at):
				async with semaphore:
					return await self._fetch_tickets_batch(s_at)

			tasks.append(fetch_with_semaphore(start_at))

		fetched_count = 0
		for future in asyncio.as_completed(tasks):
			try:
				batch = await future
				if batch:  # Check if batch is not None or empty
					for ticket in batch:
						yield ticket
						fetched_count += 1
				# Optional: Small delay can sometimes help with rate limits,
				# but semaphore should manage concurrency
				# await asyncio.sleep(0.05)
			except Exception as e:
				# Log error from a specific batch fetch but continue processing others
				logger.error('Error processing a ticket batch for project %s: %s', project_key, e)
				# Depending on requirements, you might want to raise an exception here
				# or just log and continue to get as many tickets as possible.

		logger.info(
			'Finished fetching tickets for project %s. Total yielded: %s',
			project_key,
			fetched_count,
		)

	async def get_ticket(self, ticket_id: str) -> JiraIssueContentSchema:
		"""Get a single ticket by ID or key."""
		if not ticket_id or not isinstance(ticket_id, str):
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST,
				'Invalid ticket ID or key',
			)

		url = self._build_url('issue', ticket_id)
		try:
			data = await self._make_request('GET', url, headers=self._get_auth_headers())
			return JiraIssueContentSchema.model_validate(data)
		except httpx.HTTPStatusError as e:
			if e.response.status_code == status.HTTP_404_NOT_FOUND:
				raise HTTPException(status.HTTP_404_NOT_FOUND, 'Ticket %s not found.', ticket_id)

			if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
				raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Jira authentication failed.')

			if e.response.status_code == status.HTTP_403_FORBIDDEN:
				raise HTTPException(status.HTTP_403_FORBIDDEN, 'Permission denied to view ticket.')

			raise HTTPException(
				e.response.status_code,
				'Failed to get ticket: %s',
				e.response.text,
			)
		except Exception as e:
			logger.error('Unexpected error getting ticket %s: %s', ticket_id, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR, 'Unexpected error getting ticket: %s', e
			)

	async def delete_ticket(self, ticket_id: str, delete_subtasks: bool = False) -> str:
		"""Delete a Jira ticket and optionally its subtasks.

		Args:
		    ticket_id: The ID or key of the issue to delete.
		    delete_subtasks: If True, deletes the issue's subtasks when the issue is deleted.

		Returns:
		    Success message.

		Raises:
		    HTTPException: If deletion fails or specific conditions are met (e.g., subtasks exist).
		"""
		if not ticket_id or not isinstance(ticket_id, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid ticket ID')

		url = self._build_url('issue', ticket_id)
		params = {'deleteSubtasks': str(delete_subtasks).lower()}

		try:
			response = await self.http_client.delete(
				url, headers=self._get_auth_headers(), params=params, timeout=30.0
			)

			if response.status_code == 204:
				message = f'Ticket {ticket_id} deleted successfully'
				if delete_subtasks:
					message += ' (including subtasks)'
				logger.info(message)
				return message

			# If status code is not 204, raise for status to handle errors
			response.raise_for_status()
			# Should not reach here if not 204, but as a fallback:
			logger.warning(
				'Delete request for %s returned unexpected status %s',
				ticket_id,
				response.status_code,
			)
			raise HTTPException(
				response.status_code,
				'Unexpected status code %s during deletion.',
				response.status_code,
			)

		except httpx.HTTPStatusError as e:
			error_detail = e.response.text
			try:
				# Try to parse Jira's error messages for more clarity
				error_json = e.response.json()
				messages = error_json.get('errorMessages', [])
				errors = error_json.get('errors', {})
				if messages:
					error_detail = '. '.join(messages)
				elif errors:
					# Flatten errors dict
					error_detail = '; '.join([f'{k}: {v}' for k, v in errors.items()])

			except Exception:
				pass  # Keep original text if JSON parsing fails

			status_code = e.response.status_code
			user_message = f'Failed to delete ticket {ticket_id}: {error_detail}'  # Default message

			if status_code == status.HTTP_400_BAD_REQUEST:
				user_message = (
					f'Cannot delete issue {ticket_id}. It might have subtasks. '
					f'Try again with deleteSubtasks=true. Details: {error_detail}'
				)
			elif status_code == status.HTTP_403_FORBIDDEN:
				user_message = (
					f'Permission denied to delete ticket {ticket_id}. '
					f"Check 'Delete issues' permission. Details: {error_detail}"
				)
			elif status_code == status.HTTP_404_NOT_FOUND:
				user_message = f'Ticket {ticket_id} not found.'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				user_message = 'Jira authentication failed. Please check API credentials.'

			logger.error(
				'Error deleting ticket %s (Status %s): %s', ticket_id, status_code, user_message
			)
			raise HTTPException(status_code, user_message)
		except Exception as e:
			logger.error('Unexpected error deleting ticket %s: %s', ticket_id, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				f'Failed to delete ticket due to an unexpected error: {e}',
			)

	async def get_ticket_edit_issue_metadata(self, ticket_id: str) -> dict:
		"""Get the metadata for editing a Jira ticket.

		This endpoint returns the fields that can be modified for a specific issue,
		including custom fields and their allowed values.

		Args:
		    ticket_id: The ID or key of the Jira ticket.

		Returns:
		    The ticket's editable field metadata.

		Raises:
		    HTTPException: If the request fails or the ticket is not found.
		"""
		if not ticket_id or not isinstance(ticket_id, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid ticket ID')

		url = self._build_url('issue', ticket_id, 'editmeta')

		try:
			# Use _make_request for consistency in error handling and logging
			metadata = await self._make_request('GET', url, headers=self._get_auth_headers())
			return metadata

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			detail = f'Failed to fetch edit metadata for ticket {ticket_id}: {e.response.text}'
			if status_code == status.HTTP_404_NOT_FOUND:
				detail = f'Ticket {ticket_id} not found.'
			elif status_code == status.HTTP_403_FORBIDDEN:
				detail = f'Permission denied to view edit metadata for ticket {ticket_id}.'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				detail = 'Jira authentication failed.'

			logger.error(
				'Error fetching edit metadata for %s (Status %s): %s',
				ticket_id,
				status_code,
				detail,
			)
			raise HTTPException(status_code, detail)
		except Exception as e:
			logger.error('Unexpected error fetching edit metadata for %s: %s', ticket_id, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				f'Unexpected error fetching edit metadata: {e}',
			)

	async def get_ticket_fields(self, ticket_id: str, fields: List[str]) -> Dict[str, Any]:
		"""Get specific fields for a ticket by ID or key."""
		if not ticket_id or not isinstance(ticket_id, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid ticket ID')
		if not fields:
			return {}  # Return empty if no fields requested

		url = self._build_url('issue', ticket_id)
		fields_param = ','.join(fields)
		params = {
			'fields': fields_param,
			'fieldsByKeys': 'false',  # Use field IDs for robustness
		}

		try:
			response = await self._make_request(
				'GET', url, headers=self._get_auth_headers(), params=params
			)
			# Extract only the requested fields from the 'fields' sub-dictionary
			return {
				field: response.get('fields', {}).get(field)
				for field in fields
				if 'fields' in response
			}

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			detail = f'Failed to fetch fields for ticket {ticket_id}: {e.response.text}'
			if status_code == status.HTTP_404_NOT_FOUND:
				detail = f'Ticket {ticket_id} not found.'
			elif status_code == status.HTTP_403_FORBIDDEN:
				detail = f'Permission denied to view fields for ticket {ticket_id}.'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				detail = 'Jira authentication failed.'

			logger.error(
				'Error fetching fields for %s (Status %s): %s', ticket_id, status_code, detail
			)
			raise HTTPException(status_code, detail)
		except Exception as e:
			logger.error('Unexpected error fetching fields for %s: %s', ticket_id, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				f'Unexpected error fetching ticket fields: {e}',
			)

	async def search_user(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
		"""Search for Jira users based on a query string.

		Args:
		    query: Search string to match against username, display name, or email.
		    max_results: Maximum number of users to return.

		Returns:
		    List of matched user dictionaries.

		Raises:
		    HTTPException: If the request fails or invalid parameters are provided.
		"""
		if not query or not isinstance(query, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid search query')

		# Use the findUsers endpoint for broader search capabilities
		url = self._build_url('user', 'search')
		params = {'query': query, 'maxResults': max_results}

		try:
			users_list = await self._make_request(
				'GET', url, headers=self._get_auth_headers(), params=params
			)
			# The response is directly a list of users
			return users_list if isinstance(users_list, list) else []

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			detail = f'Failed to search users: {e.response.text}'
			if status_code == status.HTTP_403_FORBIDDEN:
				detail = 'Permission denied to search users.'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				detail = 'Jira authentication failed.'
			elif status_code == status.HTTP_400_BAD_REQUEST:
				detail = f'Invalid user search request: {e.response.text}'

			logger.error('Error searching users (Status %s): %s', status_code, detail)
			raise HTTPException(status_code, detail)
		except Exception as e:
			logger.error('Unexpected error searching users: %s', e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				'Unexpected error searching users: %s',
				e,
			)

	async def get_project_boards(self, project_key_or_id: str) -> List[Dict[str, Any]]:
		"""Get all boards for a specific project using the Agile API.

		Args:
		    project_key_or_id: Project key or ID to fetch boards for.

		Returns:
		    List of board objects associated with the project.

		Raises:
		    HTTPException: If the request fails or the project is not found.
		"""
		if not project_key_or_id:
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST,
				'Project key or ID is required',
			)

		# Agile API uses a different base path
		base_url_str = str(self._get_base_url()).rstrip('/') + '/'
		agile_url = urljoin(base_url_str, 'rest/agile/1.0/board')

		params = {
			'projectKeyOrId': project_key_or_id,
			'maxResults': 100,
		}  # Fetch more boards per page
		all_boards = []
		start_at = 0

		while True:
			params['startAt'] = start_at
			try:
				response = await self._make_request(
					'GET', agile_url, headers=self._get_auth_headers(), params=params
				)

				if not isinstance(response, dict):
					logger.error('Unexpected response type for boards: %s', type(response))
					break  # Avoid infinite loop if response format is wrong

				boards = response.get('values', [])
				all_boards.extend(boards)

				if response.get('isLast', True) or not boards:  # Check if last page
					break

				start_at += len(boards)  # Go to next page

			except httpx.HTTPStatusError as e:
				status_code = e.response.status_code
				detail = (
					f'Failed to fetch project boards for {project_key_or_id}: {e.response.text}'
				)
				if status_code == status.HTTP_404_NOT_FOUND:
					detail = f'Project {project_key_or_id} not found or no boards associated.'
				elif status_code == status.HTTP_403_FORBIDDEN:
					detail = f'Permission denied to access boards for project {project_key_or_id}.'
				elif status_code == status.HTTP_401_UNAUTHORIZED:
					detail = 'Jira authentication failed.'

				logger.error('Error fetching project boards (Status %s): %s', status_code, detail)
				raise HTTPException(status_code, detail)
			except Exception as e:
				logger.error(
					'Unexpected error fetching project boards for %s: %s', project_key_or_id, e
				)
				raise HTTPException(
					status.HTTP_500_INTERNAL_SERVER_ERROR,
					f'Unexpected error fetching project boards: {e}',
				)
		return all_boards

	async def get_board_sprints(
		self, board_id: int, state: str | None = None
	) -> List[Dict[str, Any]]:
		"""Get sprints for a specific board, optionally filtered by state.

		Args:
		    board_id: The ID of the board to fetch sprints from.
		    state: Optional filter for sprint state (e.g., 'active', 'future', 'closed').

		Returns:
		    List of sprint objects.

		Raises:
		    HTTPException: If the request fails or the board is not found.
		"""
		# Agile API uses a different base path
		base_url_str = str(self._get_base_url()).rstrip('/') + '/'
		sprint_url = urljoin(base_url_str, f'rest/agile/1.0/board/{board_id}/sprint')

		params = {'maxResults': 100}  # Fetch more sprints per page
		if state:
			params['state'] = state

		all_sprints = []
		start_at = 0

		while True:
			params['startAt'] = start_at
			try:
				response = await self._make_request(
					'GET', sprint_url, headers=self._get_auth_headers(), params=params
				)

				if not isinstance(response, dict):
					logger.error('Unexpected response type for sprints: %s', type(response))
					break

				sprints = response.get('values', [])
				all_sprints.extend(sprints)

				if response.get('isLast', True) or not sprints:
					break

				start_at += len(sprints)

			except httpx.HTTPStatusError as e:
				status_code = e.response.status_code
				detail = f'Failed to fetch sprints for board {board_id}: {e.response.text}'
				if status_code == status.HTTP_404_NOT_FOUND:
					detail = f'Board {board_id} not found.'
				elif status_code == status.HTTP_403_FORBIDDEN:
					detail = f'Permission denied to access sprints for board {board_id}.'
				elif status_code == status.HTTP_401_UNAUTHORIZED:
					detail = 'Jira authentication failed.'

				logger.error('Error fetching board sprints (Status %s): %s', status_code, detail)
				raise HTTPException(status_code, detail)
			except Exception as e:
				logger.error('Unexpected error fetching sprints for board %s: %s', board_id, e)
				raise HTTPException(
					status.HTTP_500_INTERNAL_SERVER_ERROR,
					f'Unexpected error fetching board sprints: {e}',
				)
		return all_sprints

	async def find_sprint_by_name(self, sprint_name: str) -> List[Dict[str, Any]]:
		"""Find sprints by name across all boards of the client's project."""
		if not self.project or not self.project.key:
			raise ValueError(
				'Project context is required for finding sprints but was not provided '
				'during client initialization.'
			)
		project_key = self.project.key
		logger.info("Searching for sprint '%s' in project %s", sprint_name, project_key)

		try:
			boards = await self.get_project_boards(project_key)
			if not boards:
				logger.warning('No boards found for project %s to search for sprints.', project_key)
				return []

			matching_sprints = []
			sprint_fetch_tasks = [self.get_board_sprints(board['id']) for board in boards]

			# Gather sprints from all boards concurrently
			board_sprint_results = await asyncio.gather(*sprint_fetch_tasks, return_exceptions=True)

			for i, result in enumerate(board_sprint_results):
				board_name = boards[i].get('name', f'Board ID {boards[i]["id"]}')
				if isinstance(result, Exception):
					logger.error('Failed to fetch sprints for %s: %s', board_name, result)
					continue  # Skip this board if fetching sprints failed

				if isinstance(result, list):
					for sprint in result:
						# Check if sprint name contains the query (case-insensitive)
						if sprint_name.lower() in sprint.get('name', '').lower():
							matching_sprints.append({**sprint, 'board_name': board_name})

			logger.info(
				"Found %s sprints matching '%s' in project %s",
				len(matching_sprints),
				sprint_name,
				project_key,
			)
			return matching_sprints

		except Exception as e:
			# Catch exceptions from get_project_boards or other unexpected issues
			logger.error(
				"Error searching for sprint '%s' in project %s: %s", sprint_name, project_key, e
			)
			# Re-raise as a generic server error or specific exception if needed
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				'Failed to search for sprint: %s',
				e,
			)

	async def search_issue_by_name(
		self, issue_name: str, max_results: int = 10
	) -> List[Dict[str, Any]]:
		"""Search for issues by name (summary) or key within the client's project using JQL."""
		if not self.project or not self.project.key:
			raise ValueError(
				'Project context is required for searching issues but was not provided '
				'during client initialization.'
			)
		project_key = self.project.key
		logger.info("Searching for issue matching '%s' in project %s", issue_name, project_key)

		if not issue_name or not isinstance(issue_name, str):
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST,
				'Invalid issue name or key provided for search',
			)

		# Escape special JQL characters: ", \, etc.
		# Basic escaping, might need refinement based on Jira JQL syntax specifics
		escaped_name = issue_name.replace('\\', '\\\\').replace('"', '\\"')

		# Construct JQL query
		# Search in summary, description, comment, or key
		jql_parts = [f'project = {project_key}']
		# Check if it looks like a key
		if re.match(r'^[A-Z][A-Z0-9]+-\d+$', issue_name, re.IGNORECASE):
			jql_parts.append(f'key = "{escaped_name}"')
		else:
			# Search text fields - using ~ operator for contains
			jql_parts.append(
				f'(summary ~ "{escaped_name}" OR description ~ "{escaped_name}" OR comment ~ "{escaped_name}")'
			)

		jql = ' AND '.join(jql_parts)
		logger.debug('Constructed JQL for issue search: %s', jql)

		params = {
			'jql': jql,
			'maxResults': max_results,
			'fields': 'summary,status,issuetype,assignee,reporter,priority,project',
			'validateQuery': 'strict',  # Validate JQL syntax
		}

		try:
			response = await self._make_request(
				'GET',
				self._build_url('search'),
				headers=self._get_auth_headers(),
				params=params,
			)
			issues = response.get('issues', []) if isinstance(response, dict) else []
			logger.info(
				"Found %s issues matching '%s' in project %s", len(issues), issue_name, project_key
			)
			return issues

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			detail = f'Failed to search issues in project {project_key}: {e.response.text}'
			if status_code == 400:
				# Check for specific JQL errors if possible
				try:
					error_json = e.response.json()
					messages = error_json.get('errorMessages', [])
					if messages:
						detail = (
							f'Invalid JQL query for project {project_key}: {". ".join(messages)}'
						)
				except Exception:
					pass
				detail = f'Invalid search request for project {project_key}: {e.response.text}'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				detail = 'Jira authentication failed.'
			elif status_code == status.HTTP_403_FORBIDDEN:
				detail = f'Permission denied to search issues in project {project_key}.'

			logger.error('Error searching issues (Status %s): %s', status_code, detail)
			raise HTTPException(status_code, detail)
		except Exception as e:
			logger.error('Unexpected error searching issues in project %s: %s', project_key, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				f'Unexpected error searching issues: {e}',
			)

	async def update_ticket(self, ticket_id: str, payload: Dict[str, Any]) -> str:
		"""Update a Jira ticket by ID or key with the provided payload.

		Args:
		    ticket_id: The ID or key of the ticket to update.
		    payload: Dictionary containing fields to update {"fields": {"summary": "New summary"}}

		Returns:
		    Success message.

		Raises:
		    HTTPException: If the update fails.
		"""
		# Note: JiraClient doesn't strictly need project context for update if ticket_id is global,
		# but keeping the check might be intended for ensuring operations stay within a context.
		# If updates across projects are needed, this check could be removed or made conditional.
		if not self.project or not self.project.key:
			logger.warning(
				'Updating ticket %s without project context. Ensure ticket ID is correct.',
				ticket_id,
			)
			raise ValueError(
				'Project context is required for updating tickets but was not provided '
				'during client initialization.'
			)

		if not ticket_id or not isinstance(ticket_id, str):
			raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid ticket ID')

		if not payload or not isinstance(payload, dict):
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST,
				'Invalid payload for update',
			)

		url = self._build_url('issue', ticket_id)

		try:
			response = await self.http_client.put(
				url, headers=self._get_auth_headers(), json=payload, timeout=30.0
			)

			# Jira returns 204 No Content on successful update
			if response.status_code == 204:
				logger.info('Ticket %s updated successfully.', ticket_id)
				return f'Ticket {ticket_id} updated successfully'

			# If not 204, raise for status to handle errors
			response.raise_for_status()
			logger.warning(
				'Update request for %s returned unexpected status %s',
				ticket_id,
				response.status_code,
			)
			raise HTTPException(
				response.status_code,
				f'Unexpected status code {response.status_code} during update.',
			)

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			error_detail = e.response.text
			try:
				error_json = e.response.json()
				messages = error_json.get('errorMessages', [])
				errors = error_json.get('errors', {})
				if messages:
					error_detail = '. '.join(messages)
				elif errors:
					error_detail = '; '.join([f'{k}: {v}' for k, v in errors.items()])
			except Exception:
				pass

			user_message = f'Failed to update ticket {ticket_id}: {error_detail}'  # Default

			if status_code == status.HTTP_400_BAD_REQUEST:
				user_message = (
					f'Invalid update request for ticket {ticket_id}. '
					f'Check payload format and field values. Details: {error_detail}'
				)
			elif status_code == status.HTTP_404_NOT_FOUND:
				user_message = f'Ticket {ticket_id} not found.'
			elif status_code == status.HTTP_403_FORBIDDEN:
				user_message = f'Permission denied to update ticket {ticket_id}.'
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				user_message = 'Jira authentication failed.'

			logger.error(
				'Error updating ticket %s (Status %s): %s', ticket_id, status_code, user_message
			)
			raise HTTPException(status_code, user_message)
		except Exception as e:
			logger.error('Unexpected error updating ticket %s: %s', ticket_id, e)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				f'Failed to update ticket due to an unexpected error: {e}',
			)

	async def revert_ticket_changes(self, ticket_id: str, version_id: str) -> Dict[str, Any]:
		"""Revert a Jira ticket to a specific version (using changelog/history - conceptual).

		NOTE: Jira API does not have a direct 'revert to version' endpoint.
		This method would need to be implemented by:
		1. Fetching the changelog/history for the ticket.
		2. Identifying the state of the fields at the specified version_id.
		3. Constructing an update payload to set the fields back to that state.
		4. Calling the `update_ticket` method with the constructed payload.

		This is a complex operation and highly dependent on specific field types and history format.
		The current implementation is a placeholder.

		Args:
		    ticket_id: The ID or key of the ticket.
		    version_id: The ID of the history record or changelog entry to revert to.

		Returns:
		    Result of the update operation.

		Raises:
		    NotImplementedError: As this feature is complex and not directly supported.
		    HTTPException: If underlying operations fail.
		"""
		logger.warning(
			'Revert functionality for ticket %s to version %s is not fully implemented.',
			ticket_id,
			version_id,
		)
		# Placeholder - requires fetching history, comparing fields, and constructing update payload
		raise NotImplementedError(
			'Direct revert to version via Jira API is not supported. Manual implementation required.'
		)

		# Example conceptual steps (would need actual implementation):
		# 1. history = await self.get_ticket_history(ticket_id)
		# 2. target_state = self.find_state_at_version(history, version_id)
		# 3. update_payload = self.construct_revert_payload(target_state)
		# 4. return await self.update_ticket(ticket_id, update_payload)

	async def get_issue_createmeta(
		self,
		project_key: str,
		issue_type: str,
		expand: str = 'projects.issuetypes.fields',
	) -> dict:
		"""Get metadata required to create an issue (fields, allowed values).

		Args:
		    project_key: The key of the project.
		    issue_type: The name of the issue type (e.g., "Bug", "Task").
		    expand: Optional fields to expand in the response for more detail.

		Returns:
		    Dictionary containing createmeta information.

		Raises:
		    HTTPException: If fetching metadata fails.
		"""
		self._validate_project_key(project_key)
		if not issue_type:
			raise HTTPException(
				status.HTTP_400_BAD_REQUEST, 'Issue type name is required for createmeta.'
			)

		url = self._build_url('issue', 'createmeta')
		params = {
			'projectKeys': project_key,
			'issuetypeNames': issue_type,
			'expand': expand,
		}

		try:
			metadata = await self._make_request(
				'GET', url, headers=self._get_auth_headers(), params=params
			)
			# The response contains a 'projects' list, usually with one project matching the key
			if isinstance(metadata, dict) and metadata.get('projects'):
				project_meta = metadata['projects'][0]  # Assume first project is the one requested
				issue_types = project_meta.get('issuetypes', [])
				if issue_types:
					# Return the metadata for the first (and likely only) issue type returned
					return issue_types[0]

				raise HTTPException(
					status.HTTP_404_NOT_FOUND,
					f"Issue type '{issue_type}' not found or available in project '{project_key}' for creation.",
				)

			logger.error(
				'Unexpected createmeta response format for %s/%s: %s',
				project_key,
				issue_type,
				metadata,
			)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				'Unexpected response format from Jira createmeta.',
			)

		except httpx.HTTPStatusError as e:
			status_code = e.response.status_code
			detail = f'Failed to fetch createmeta for {project_key}/{issue_type}: {e.response.text}'
			if status_code == status.HTTP_400_BAD_REQUEST:
				detail = (
					f'Invalid request for createmeta (check project key/issue type name): '
					f'{e.response.text}'
				)
			elif status_code == status.HTTP_401_UNAUTHORIZED:
				detail = 'Jira authentication failed.'
			elif status_code == status.HTTP_403_FORBIDDEN:
				detail = f'Permission denied to fetch createmeta for project {project_key}.'

			logger.error('Error fetching createmeta (Status %s): %s', status_code, detail)
			raise HTTPException(status_code, detail)
		except Exception as e:
			logger.error(
				'Unexpected error fetching createmeta for %s/%s: %s', project_key, issue_type, e
			)
			raise HTTPException(
				status.HTTP_500_INTERNAL_SERVER_ERROR,
				'Unexpected error fetching createmeta: %s',
				e,
			)

	async def create_ticket(self, payload: dict) -> dict:
		"""
		Creates a Jira ticket.

		Args:
		    payload: The request body for ticket creation.

		Returns:
		    A dictionary with 'key', 'id', and 'url' of the created ticket.

		Raises:
		    HTTPException: If the input payload is invalid.
		    ValueError: If the successful response from Jira is missing expected fields ('key', 'id').
		    httpx.HTTPStatusError: If Jira returns a 4xx or 5xx status.
		    httpx.RequestError: If there's a connection error, timeout, etc.
		    json.JSONDecodeError: If Jira's response is not valid JSON.
		    Exception: For any other unexpected errors.
		"""
		url = self._build_url('issue')

		response_data = await self._make_request(
			'POST',
			url,
			headers=self._get_auth_headers(),
			json=payload,
			timeout=30.0,
		)

		# Add a user-friendly link to the response, as Jira's response doesn't include it FFS
		if response_data and 'key' in response_data:
			base_url = str(self._get_base_url()).rstrip('/')
			response_data['link'] = f'{base_url}/browse/{response_data["key"]}'

		return response_data

	async def get_issue_types(
		self, project_key: str | None = None, names_only: bool = False, simplified: bool = True
	) -> Union[List[Dict[str, Any]], List[str]]:
		"""Get available issue types, optionally filtered by project.

		Args:
			project_key: Optional project key to filter issue types. If None, uses client's project context.
			names_only: If True, returns only a list of issue type names. Otherwise, returns full objects.
			simplified: If True, returns only a subset of fields for each issue type
									('self', 'description', 'name', 'subtask', 'hierarchyLevel').

		Returns:
			List of issue type dictionaries or list of issue type names.

		Raises:
			ValueError: If project context is needed but not available.
			HTTPException: If fetching issue types fails.
		"""
		project_url = self._build_url('project', project_key)
		project_data = await self._make_request(
			'GET', project_url, headers=self._get_auth_headers()
		)

		issue_types = project_data.get('issueTypes', [])

		if names_only:
			return [it.get('name', 'Unknown') for it in issue_types if isinstance(it, dict)]

		if simplified:
			simplified_types = []
			for issue_type in issue_types:
				if isinstance(issue_type, dict):
					simplified_type = {
						'self': issue_type.get('self'),
						'description': issue_type.get('description'),
						'name': issue_type.get('name'),
						'subtask': issue_type.get('subtask'),
						'hierarchyLevel': issue_type.get('hierarchyLevel'),
					}
					simplified_types.append(simplified_type)
			return simplified_types

		return issue_types

	def _parse_create_errors(self, e: httpx.HTTPStatusError) -> str:
		"""Parse specific Jira errors for ticket creation for better user feedback."""
		try:
			error_data = e.response.json()
			messages = error_data.get('errorMessages', [])
			errors = error_data.get('errors', {})

			if messages:
				# General error messages
				return '. '.join(messages)
			if errors:
				# Field-specific errors
				field_errors = []
				for field, message in errors.items():
					field_errors.append(f"Field '{field}': {message}")
				return '. '.join(field_errors)

			# Fallback if structure is unexpected
			return e.response.text

		except Exception:
			# If response is not JSON or parsing fails
			return e.response.text

	async def get_user_by_email(self, email: str) -> str | None:
		"""Get a user's accountId by their email address.

		Args:
			email: The email address of the user to find.

		Returns:
			The user's accountId if found, None otherwise.
		"""
		if not email or not isinstance(email, str):
			logger.warning('Invalid email provided for user lookup')
			return None

		try:
			# Use the user search endpoint with the email as query
			url = self._build_url('user', 'search')
			params = {'query': email}

			users = await self._make_request(
				'GET', url, headers=self._get_auth_headers(), params=params
			)

			if not users or not isinstance(users, list):
				logger.warning('No users found for email: %s', email)
				return None

			# Find the user with matching email
			for user in users:
				if isinstance(user, dict) and user.get('emailAddress') == email:
					return user.get('accountId')

			logger.warning('No exact email match found for: %s', email)
			return None

		except Exception as e:
			logger.warning('Error finding user by email %s: %s', email, e)
			return None

	async def get_project_context(self) -> Dict[str, Any]:
		"""Get comprehensive project context for LLM processing.

		Returns a dictionary containing:
		- project_metadata: Basic project information
		- available_issue_types: Supported ticket types in this project
		- user_context: Current user permissions and roles
		"""
		if not self.project:
			return {'error': 'No project context available', 'available_issue_types': []}

		# Get available issue types for this project
		try:
			issue_types = await self.get_issue_types(self.project.key)
		except Exception as e:
			logger.warning('Failed to fetch issue types for context: %s', e)
			issue_types = []

		# Get user account ID from email
		user_email = self.api_key.domain_email
		user_account_id = None

		try:
			user_account_id = await self.get_user_by_email(user_email)
		except Exception as e:
			logger.warning('Failed to fetch user accountId for %s: %s', user_email, e)

		if not user_account_id:
			user_account_id = user_email
			logger.info('Using email as fallback for accountId: %s', user_email)

		return {
			'project_metadata': {
				'key': self.project.key,
				'name': self.project.name,
				'id': self.project.id,
			},
			'available_issue_types': issue_types,
			'user_context': {'account_id': user_account_id},
		}
