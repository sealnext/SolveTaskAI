from data_extractor import DataExtractorFactory

class DataExtractorFacade:
  """
  Facade class for Data Extractor component.
  """

  def __new__(cls, *args, **kwargs):
    raise TypeError(f"Cannot instantiate {cls.__name__}. Use its static methods instead.")

  @staticmethod
  def get_projects():
    data_extractor = DataExtractorFactory.create_data_extractor()
    return data_extractor.get_all_projects()
