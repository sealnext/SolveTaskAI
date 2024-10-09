from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from models.apikey import APIKey


class TicketingSystemType(Enum):
  """
  Enum defining the ticketing platforms we support.
  """
  JIRA = "JIRA"
  AZURE = "AZURE"

  @staticmethod
  def from_string(enum_string: str) -> 'TicketingSystemType':
    try:
      return TicketingSystemType[enum_string.upper()]
    except KeyError:
      raise ValueError(f"{enum_string} is not a valid TicketingSystemType or not supported.")


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
  async def get_all_tickets(self, project_key: str):
    pass
