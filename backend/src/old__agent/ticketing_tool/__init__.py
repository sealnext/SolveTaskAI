from config.enums import TicketingSystemType
from .jira_client import JiraClient
# from .azure_client import AzureClient  # To be implemented
from schemas import APIKey, Project

async def create_ticketing_client(api_key: APIKey, project: Project):
    """
    Factory function to create the appropriate ticketing client based on project type.
    
    Args:
        api_key: APIKeySchema instance containing API key details
        project: Project model instance with loaded relationships
        
    Returns:
        Appropriate ticketing client instance (JiraClient, AzureClient, etc.)
        
    Raises:
        ValueError: If ticketing system is not supported
    """
    if project.service_type == TicketingSystemType.JIRA:
        return JiraClient(
            domain=project.domain,
            api_key=api_key.api_key,  # Using the correct column name from APIKey model
            project_key=project.key,
            domain_email=api_key.domain_email
        )
    
    elif project.service_type == TicketingSystemType.AZURE:
        # To be implemented
        # return AzureClient(project.domain, project.key, credentials)
        raise NotImplementedError("Azure DevOps integration not implemented yet")
    
    else:
        raise ValueError(f"Unsupported ticketing system: {project.service_type}") 