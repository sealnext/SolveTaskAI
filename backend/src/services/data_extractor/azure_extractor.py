from .interfaces.data_extractor_interface import DataExtractor


class DataExtractorAzure(DataExtractor):
  """
  Implementation class for Microsoft Azure DevOps - Azure Boards platform.
  """

  def __init__(self):
    raise NotImplementedError(f"Class {self.__class__.__name__} is not implemented yet.")

  async def get_total_tickets(self, project_key: str) -> int:
    """Get total number of tickets in a project.
    
    Args:
        project_key: The project key to get tickets for
        
    Returns:
        int: Total number of tickets in the project
    """
    # TODO: Implement Azure DevOps specific logic
    # For now return a default value
    return 1000