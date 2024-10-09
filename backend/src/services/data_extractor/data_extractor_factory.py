from .data_extractor import TicketingSystemType, DataExtractor
from .details import DataExtractorJira, DataExtractorAzure
from models.apikey import APIKey

import os
from urllib.parse import urljoin


class DataExtractorFactory:
  """
  Factory class used for creating DataExtractor objects.
  """

  @staticmethod
  async def create_data_extractor(api_key: APIKey) -> DataExtractor:
    ticketing_system_type = TicketingSystemType.from_string(api_key.project.ticketing_system_type)

    if ticketing_system_type == TicketingSystemType.JIRA:
      return DataExtractorJira(api_key)
    elif ticketing_system_type == TicketingSystemType.AZURE:
      return DataExtractorAzure(api_key)
    else:
      raise NotImplementedError(f"{ticketing_system_type.value} is not implemented yet")


  @staticmethod
  def _create_data_extractor_jira(ticketing_platform_url: str, username: str, password: str) -> DataExtractorJira:
    ticketing_api_url = urljoin(ticketing_platform_url, "/rest/api/3")
    return DataExtractorJira(ticketing_api_url, username, password)


  @staticmethod
  def _create_data_extractor_azure() -> DataExtractorAzure:
    return DataExtractorAzure()
