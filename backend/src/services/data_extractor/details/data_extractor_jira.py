from ..data_extractor import DataExtractor
from models.apikey import APIKey
import aiohttp
from urllib.parse import urljoin


class DataExtractorJira(DataExtractor):
  """
  Implementation class for Attlasian Jira platform.
  """

  def __init__(self, api_key: APIKey):
    super().__init__(api_key)
    self.base_api_url = urljoin(api_key.project.jira_url, "/rest/api/3")
    self.auth = aiohttp.BasicAuth(api_key.user.email, api_key.api_key)

  async def get_all_projects(self):
    api_route = urljoin(self.base_api_url, "/project")
    async with aiohttp.ClientSession(auth=self.auth) as session:
      async with session.get(api_route) as response:
        if response.status == 200:
          return await response.json()
        else:
          raise Exception(f"Failed to fetch projects: {response.status}, {await response.text()}")

  async def get_all_tickets(self, project_key: str):
    api_route = urljoin(self.base_api_url, "/search")
    query_params = {
      'jql': f'project={project_key}',
      'maxResults': 50
    }
    async with aiohttp.ClientSession(auth=self.auth) as session:
      async with session.get(api_route, params=query_params) as response:
        if response.status == 200:
          return await response.json()
        else:
          raise Exception(f"Failed to fetch tickets: {response.status}, {await response.text()}")

