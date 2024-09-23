from .data_extractor import TicketingSystemType, DataExtractor
from .details import DataExtractorJira, DataExtractorAzure

import os
from urllib.parse import urljoin


class DataExtractorFactory:
  """
  Factory class used for creating DataExtractor objects.
  """

  @staticmethod
  def create_data_extractor() -> DataExtractor:
    ticketing_system_type = TicketingSystemType.from_string(os.getenv("TICKETING_PLATFORM"))
    ticketing_platform_url = os.getenv("TICKETING_PLATFORM_URL")
    username = os.getenv("USERNAME")
    password = os.getenv("ACCESS_TOKEN")

    if ticketing_system_type == TicketingSystemType.JIRA:
      return DataExtractorFactory._create_data_extractor_jira(ticketing_platform_url, username, password)

    elif ticketing_system_type == TicketingSystemType.AZURE:
      return DataExtractorFactory._create_data_extractor_azure(ticketing_platform_url, username, password)

    else:
      raise NotImplementedError(f"{ticketing_system_type.value} is not implemented yet")


  @staticmethod
  def _create_data_extractor_jira(ticketing_platform_url: str, username: str, password: str) -> DataExtractorJira:
    ticketing_api_url = urljoin(ticketing_platform_url, "/rest/api/2")
    return DataExtractorJira(ticketing_api_url, username, password)


  @staticmethod
  def _create_data_extractor_azure() -> DataExtractorAzure:
    return DataExtractorAzure()
