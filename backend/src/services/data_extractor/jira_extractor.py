from .interfaces.data_extractor_interface import DataExtractor
from models.apikey import APIKey
import aiohttp
from urllib.parse import urljoin


class DataExtractorJira(DataExtractor):
  """
  Implementation class for Attlasian Jira platform.
  """

  def __init__(self, api_key: APIKey):
    super().__init__(api_key)
    self.base_api_url = urljoin(api_key.domain, "/rest/api/2/")
    self.auth = aiohttp.BasicAuth(api_key.domain_email, api_key.api_key)

  async def get_all_projects(self):
    api_route = urljoin(self.base_api_url, "project/search")
    print("api_route", api_route)
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
          all_projects.extend(data['values'])
          
          if data['isLast']:
            break
        
        start_at += max_results

    return all_projects

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

