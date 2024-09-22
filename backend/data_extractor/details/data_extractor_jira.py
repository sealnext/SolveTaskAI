from data_extractor import DataExtractor
import requests
from urllib.parse import urljoin


class DataExtractorJira(DataExtractor):
  """
  Implementation class for Attlasian Jira platform.
  """

  def __init__(self, base_api_url: str, username: str, access_token: str):
    self.base_api_url = base_api_url
    self.session = requests.Session()
    self.session.auth = requests.auth.HTTPBasicAuth(username, access_token)


  def get_all_projects(self):
    api_route = urljoin(self.base_api_url, "/project")  # Changed from url_join to urljoin
    response = self.session.get(api_route)

    if response.status_code == 200:
      return response.json()
    else:
      raise Exception(f"Failed to fetch projects: {response.status_code}, {response.text}")


  def get_all_tickets(self, project_key: str):
    api_route = urljoin(self.base_api_url, "/search")  # Changed from url_join to urljoin
    query_params = {
      'jql': f'project={project_key}',
      'maxResults': 50
    }
    response = self.session.get(api_route, params=query_params)

    if response.status_code == 200:
      return response.json()
    else:
      raise Exception(f"Failed to fetch tickets: {response.status_code}, {response.text}")

