import aiohttp
import asyncio
import logging
import tenacity
from urllib.parse import urljoin
from typing import List, Dict, Any, Tuple, Union, AsyncGenerator, AsyncIterator, Optional
from .interfaces.data_extractor_interface import DataExtractor
from schemas import ExternalProjectSchema, JiraIssueSchema, JiraIssueContentSchema, APIKeySchema
from config import (
    JIRA_MAX_CONCURRENT_REQUESTS,
    JIRA_MAX_RESULTS_PER_PAGE,
    JIRA_RETRY_ATTEMPTS,
    JIRA_RETRY_DELAY
)
from aiohttp import ClientSession, ClientTimeout
from aiostream import stream, pipe

logger = logging.getLogger(__name__)

class JiraAPIError(Exception):
    """Custom exception for Jira API errors with status code and message."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"Jira API error {status}: {message}")

class DataExtractorJira(DataExtractor):
    """Jira implementation of the DataExtractor interface with optimized async processing."""
    def __init__(self, api_key: APIKeySchema):
        super().__init__(api_key)
        self.api_key = api_key
        self.base_api_url = urljoin(api_key.domain, "/rest/api/2/")
        self.auth = aiohttp.BasicAuth(api_key.domain_email, api_key.api_key)
        self._session: Optional[ClientSession] = None
        self._semaphore = asyncio.Semaphore(JIRA_MAX_CONCURRENT_REQUESTS)
        
    async def __aenter__(self):
        timeout = ClientTimeout(total=30)
        self._session = ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None
            
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(JIRA_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=JIRA_RETRY_DELAY, min=JIRA_RETRY_DELAY, max=10),
        retry=tenacity.retry_if_exception_type((
            aiohttp.ClientError,
            asyncio.TimeoutError,
            aiohttp.ServerTimeoutError,
            JiraAPIError
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying Jira API call in {retry_state.next_action.sleep} seconds..."
        )
    )
    async def fetch_with_retry(self, 
                             session: aiohttp.ClientSession, 
                             url: str, 
                             params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from Jira API with retries for specific errors.
        Handles network errors, timeouts, and Jira-specific errors.
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
            async with session.get(url, params=params, timeout=timeout) as response:
                if response.status == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', JIRA_RETRY_DELAY))
                    raise JiraAPIError(429, f"Rate limited. Retry after {retry_after} seconds")
                elif response.status == 503:  # Service Unavailable
                    raise JiraAPIError(503, "Jira service temporarily unavailable")
                elif response.status != 200:
                    error_text = await response.text()
                    raise JiraAPIError(response.status, f"Failed to fetch data: {error_text}")
                
                return await response.json()
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching from {url}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching from {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching from {url}: {str(e)}")
            raise

    async def get_ticket(self, ticket_url: str) -> JiraIssueContentSchema:
        async with aiohttp.ClientSession(auth=self.auth) as session:
            logger.info(f"Fetching ticket from {ticket_url}")
            data = await self.fetch_with_retry(session, ticket_url, params={})
            logger.info(f"Successfully fetched ticket {ticket_url}")
            project_id = str(data.get('fields', {}).get('project', {}).get('id'))
            logger.info(f"Project ID: {project_id}")
            return JiraIssueContentSchema(**{**data, 'project_id': project_id})

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
                
                if len(data['values']) < max_results:
                    break
                
                start_at += max_results

        return all_projects

    async def _fetch_ticket_batch(self, session: aiohttp.ClientSession, 
                                project_key: str, project_id: str,
                                start_at: int) -> Tuple[List[JiraIssueSchema], int, int]:
        """Fetch a batch of tickets starting from a specific index."""
        params = {
            'jql': f'project={project_key}',
            'startAt': start_at,
            'maxResults': JIRA_MAX_RESULTS_PER_PAGE,
            'fields': '*all'
        }

        logger.debug(f"Fetching tickets batch starting at {start_at} for project {project_key}")
        data = await self.fetch_with_retry(session, urljoin(self.base_api_url, "search"), params=params)
        
        tickets = [
            JiraIssueSchema(**{**issue, 'project_id': str(project_id)})
            for issue in data['issues']
        ]
        return tickets, len(data['issues']), data['total']

    async def _fetch_tickets_generator(self, 
                                    session: aiohttp.ClientSession,
                                    project_key: str,
                                    project_id: str,
                                    start_at: int = 0) -> AsyncGenerator[List[JiraIssueSchema], None]:
        """
        Async generator that yields batches of tickets.
        Memory efficient as it doesn't hold all tickets in memory at once.
        """
        while True:
            tickets, batch_size, total = await self._fetch_ticket_batch(
                session, project_key, project_id, start_at
            )
            
            if not tickets:
                break
                
            yield tickets
            
            start_at += batch_size
            if start_at >= total:
                break
            
            # Small delay to prevent overwhelming the Jira API
            await asyncio.sleep(0.1)
      
    async def get_all_tickets(self, project_key: str, project_id: str) -> AsyncGenerator[List[JiraIssueSchema], None]:
        """
        Get all tickets for a project using memory efficient async generator.
        Yields batches of tickets as they are fetched.
        """
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async for batch in self._fetch_tickets_generator(session, project_key, project_id):
                yield batch
                logger.debug(f"Yielded batch of {len(batch)} tickets for project {project_key}")

    async def get_all_tickets_list(self, project_key: str, project_id: str) -> List[JiraIssueSchema]:
        """
        Legacy method that returns all tickets as a list.
        Warning: This method loads all tickets into memory.
        Use get_all_tickets() generator version for better memory efficiency.
        """
        all_tickets = []
        async for batch in self.get_all_tickets(project_key, project_id):
            all_tickets.extend(batch)
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
            semaphore = asyncio.Semaphore(JIRA_MAX_CONCURRENT_REQUESTS)
            
            async def fetch_with_semaphore(url: str) -> JiraIssueContentSchema:
                async with semaphore:
                    return await self.fetch_ticket(session, url)
            
            return await asyncio.gather(*[
                fetch_with_semaphore(url) for url in ticket_urls
            ])

    async def get_tickets(self, api_key: APIKeySchema, project_key: str) -> AsyncIterator[JiraIssueSchema]:
        """
        Fetch tickets from Jira using async generator for memory efficiency.
        Yields tickets as they are fetched, processing in batches.
        """
        if not self._session:
            raise RuntimeError("JiraExtractor must be used as a context manager")
            
        # Get total number of tickets first
        total = await self._get_total_tickets(api_key, project_key)
        logger.info(f"Found {total} tickets for project {project_key}")
        
        if total == 0:
            return
            
        # Create optimized stream for fetching tickets
        start_ats = range(0, total, JIRA_MAX_RESULTS_PER_PAGE)
        
        # Convert to stream and process concurrently
        request_stream = (
            stream.iterate(start_ats)
            | pipe.map(lambda start: self._fetch_tickets_batch(api_key, project_key, start))
            | pipe.merge(task_limit=JIRA_MAX_CONCURRENT_REQUESTS)
        )
        
        # Yield tickets as they arrive
        async with stream.iterate(request_stream) as streamer:
            async for tickets in streamer:
                for ticket in tickets:
                    yield ticket
                    
    async def _get_total_tickets(self, api_key: APIKeySchema, project_key: str) -> int:
        """Get total number of tickets in project."""
        params = {
            "jql": f"project = {project_key}",
            "maxResults": 0
        }
        async with self._semaphore:
            response = await self._make_request(api_key, "search", params)
            return response["total"]
            
    async def _fetch_tickets_batch(self, api_key: APIKeySchema, project_key: str, start_at: int) -> List[JiraIssueSchema]:
        """Fetch a batch of tickets with retry logic."""
        params = {
            "jql": f"project = {project_key}",
            "maxResults": JIRA_MAX_RESULTS_PER_PAGE,
            "startAt": start_at,
            "fields": "summary,description,created,updated,status,priority,issuetype"
        }
        
        async with self._semaphore:
            try:
                response = await self._make_request(api_key, "search", params)
                issues = response.get("issues", [])
                return [JiraIssueSchema.model_validate(issue) for issue in issues]
            except Exception as e:
                logger.error(f"Error fetching tickets batch at {start_at}: {str(e)}")
                raise
                
    async def _make_request(self, api_key: APIKeySchema, endpoint: str, params: dict) -> dict:
        """Make authenticated request to Jira API with retry logic."""
        headers = {
            "Authorization": f"Basic {api_key.api_key}",
            "Accept": "application/json"
        }
        
        url = f"https://{api_key.domain}/rest/api/2/{endpoint}"
        
        for attempt in range(3):  # Simple retry logic
            try:
                async with self._session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"Failed to make request after 3 attempts: {str(e)}")
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

    async def get_total_tickets(self, project_key: str) -> int:
        """Get total number of tickets in a project.
        
        Args:
            project_key: The project key to get tickets for
            
        Returns:
            int: Total number of tickets in the project
        """
        params = {
            'jql': f'project={project_key}',
            'maxResults': 0  # We only need the total count
        }
        
        async with aiohttp.ClientSession(auth=self.auth) as session:
            data = await self.fetch_with_retry(session, urljoin(self.base_api_url, "search"), params=params)
            total = data.get('total', 0)
            logger.info(f"Found {total} total tickets for project {project_key}")
            return total
