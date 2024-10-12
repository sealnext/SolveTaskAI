from .interfaces.data_extractor_interface import DataExtractor
from models.apikey import APIKey
from validation_models import ExternalProjectSchema, APIKeySchema
import aiohttp
from urllib.parse import urljoin
from typing import List, Dict, Any
from .interfaces.data_extractor_interface import DataExtractor


class DataExtractorJira(DataExtractor):
  """
  Implementation class for Attlasian Jira platform.
  """

  def __init__(self, api_key: APIKeySchema):
    super().__init__(api_key)
    self.api_key = api_key
    self.base_api_url = urljoin(api_key.domain, "/rest/api/2/")
    self.auth = aiohttp.BasicAuth(api_key.domain_email, api_key.api_key)

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
        async with session.get(api_route, params=params) as response:
          if response.status != 200:
            raise Exception(f"Failed to fetch projects: {response.status}, {await response.text()}")
          
          data = await response.json()
          all_projects.extend(self._standardize_project_data(data['values']))
          
          if data['isLast']:
            break
        
        start_at += max_results

    return all_projects

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

  async def get_all_tickets(self, project_key: str):
    api_route = urljoin(self.base_api_url, "/search")
    all_tickets = []
    start_at = 0
    max_results = 50

    async with aiohttp.ClientSession(auth=self.auth) as session:
      while True:
        params = {
          'jql': f'project={project_key}',
          'startAt': start_at,
          'maxResults': max_results
        }
        async with session.get(api_route, params=params) as response:
          if response.status != 200:
            raise Exception(f"Failed to fetch tickets: {response.status}, {await response.text()}")
          
          data = await response.json()
          all_tickets.extend(data['issues'])
          
          if len(data['issues']) < max_results:
            break
        
        start_at += max_results

    return all_tickets
