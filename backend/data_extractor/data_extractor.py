from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod


class TicketingSystemType(Enum):
  """
  Enum defining the ticketing platforms we support.
  """
  JIRA = "JIRA"
  AZURE = "AZURE"

  @staticmethod
  def from_string(enum_string: str) -> TicketingSystemType:
    try:
      return TicketingSystemType[enum_string]
    except KeyError:
      raise ValueError(f"{enum_string} is not a valid TicketingSystemType or not supported.")


class DataExtractor(ABC):
  """
  Interface used for extracing data (tickets, documents) from ticketing platforms.
  """

  @abstractmethod
  def get_all_projects(self):
    pass

  @abstractmethod
  def get_all_tickets(self, project_key: str):
    pass
