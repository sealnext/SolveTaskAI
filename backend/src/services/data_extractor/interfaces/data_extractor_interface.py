from __future__ import annotations
from abc import ABC, abstractmethod
from models.apikey import APIKey

class DataExtractor(ABC):
  """
  Interface used for extracing data (tickets, documents) from ticketing platforms.
  """

  def __init__(self, api_key: APIKey):
    self.api_key = api_key

  @abstractmethod
  async def get_all_projects(self):
    pass

  @abstractmethod
  async def get_all_tickets(self, project_key: str, project_id: int):
    pass
