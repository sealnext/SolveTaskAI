import aiohttp
import asyncio
import logging
from urllib.parse import urljoin
from typing import List, Dict, Any
from .interfaces.data_extractor_interface import DataExtractor
from schemas import ExternalProjectSchema, JiraIssueSchema, JiraIssueContentSchema

logger = logging.getLogger(__name__)

class DataExtractorJira(DataExtractor):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.api_key = api_key
        self.base_api_url = urljoin(api_key.domain, "/rest/api/2/")
        self.auth = aiohttp.BasicAuth(api_key.domain_email, api_key.api_key)

    async def fetch_with_retry(self, session, url, params, retries=3, delay=1):
        for attempt in range(retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch data: {response.status}, {await response.text()}")
                    return await response.json()
            except Exception as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    async def get_ticket(self, ticket_url: str) -> JiraIssueContentSchema:
        async with aiohttp.ClientSession(auth=self.auth) as session:
            logger.info(f"Fetching ticket from {ticket_url}")

            data = await self.fetch_with_retry(session, ticket_url, params={})

            logger.info(f"Successfully fetched ticket {ticket_url}")

            project_id = str(data.get('fields', {}).get('project', {}).get('id'))

            logger.info(f"Project ID: {project_id}")

            validated_ticket = JiraIssueContentSchema(**{**data, 'project_id': project_id})

            return validated_ticket

    async def get_all_projects(self) -> List[ExternalProjectSchema]:
        api_route = urljoin(self.base_api_url, "project/search")
        all_projects = []
        start_at = 0
        max_results = 50

        async with aiohttp.ClientSession(auth=self.auth) as session:
            while True:
                params = {
                    'startAt': start_at,
                    'maxResults': max_results
                }

                logger.info(f"Fetching projects starting at {start_at}")

                data = await self.fetch_with_retry(session, api_route, params=params)
                all_projects.extend(self._standardize_project_data(data['values']))

                if len(data['values']) < max_results:  # No more pages
                    break

                start_at += max_results

        return all_projects

    async def get_all_tickets(self, project_key: str, project_id: str) -> List[JiraIssueSchema]:
        api_route = urljoin(self.base_api_url, "search")
        all_tickets = []
        start_at = 0
        max_results = 100

        async with aiohttp.ClientSession(auth=self.auth) as session:
            while True:
                params = {
                    'jql': f'project={project_key}',
                    'startAt': start_at,
                    'maxResults': max_results,
                    'fields': '*all'
                }

                logger.info(f"Fetching tickets starting at {start_at} for project {project_key}")

                data = await self.fetch_with_retry(session, api_route, params=params)

                # Convert and validate tickets as we receive them
                validated_tickets = [
                    JiraIssueSchema(**{**issue, 'project_id': str(project_id)})
                    for issue in data['issues']
                ]
                all_tickets.extend(validated_tickets)

                if len(data['issues']) < max_results:
                    break  # Stop if there are no more tickets to fetch

                start_at += max_results

        return all_tickets

    def _standardize_project_data(self, projects: List[Dict[str, Any]]) -> List[ExternalProjectSchema]:
        return [
            ExternalProjectSchema(
                name=project.get("name"),
                key=project.get("key"),
                id=project.get("id"),
                avatarUrl=project.get("avatarUrls", {}).get("48x48"),
                projectTypeKey=project.get("projectTypeKey"),
                style=project.get("style")
            )
            for project in projects
        ]

    async def get_tickets_parallel(self, ticket_urls: List[str]) -> List[JiraIssueContentSchema]:
        async with aiohttp.ClientSession(auth=self.auth) as session:
            tasks = [self.fetch_ticket(session, url) for url in ticket_urls]
            return await asyncio.gather(*tasks)

    async def fetch_ticket(self, session, ticket_url: str) -> JiraIssueContentSchema:
        logger.info(f"Fetching ticket from {ticket_url}")
        data = await self.fetch_with_retry(session, ticket_url, params={})
        project_id = str(data.get('fields', {}).get('project', {}).get('id'))
        return JiraIssueContentSchema(**{**data, 'project_id': project_id})
