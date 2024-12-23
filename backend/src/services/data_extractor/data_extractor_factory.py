from .interfaces.data_extractor_interface import DataExtractor
from .jira_extractor import DataExtractorJira
from .azure_extractor import DataExtractorAzure
from schemas import APIKeySchema
from config.enums import TicketingSystemType
    
def create_data_extractor(api_key: APIKeySchema) -> DataExtractor:
    ticketing_system_type = TicketingSystemType(api_key.service_type)

    if ticketing_system_type == TicketingSystemType.JIRA:
        return DataExtractorJira(api_key)
    elif ticketing_system_type == TicketingSystemType.AZURE:
        return DataExtractorAzure(api_key)
    else:
        raise NotImplementedError(f"{ticketing_system_type.value} is not implemented yet")