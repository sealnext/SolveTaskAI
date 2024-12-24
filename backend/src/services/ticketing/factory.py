from typing import Dict, Type
import httpx
from pydantic import BaseModel
from schemas import APIKeySchema
from .client import BaseTicketingClient
from .implementations.jira import JiraClient
from .implementations.azure import AzureClient
from models.apikey import TicketingSystemType
import asyncio
from httpx import Limits, Timeout
from config import JIRA_MAX_CONCURRENT_REQUESTS

class TicketingConfig(BaseModel):
    """Configuration for ticketing clients."""
    max_connections: int = JIRA_MAX_CONCURRENT_REQUESTS
    max_keepalive_connections: int = JIRA_MAX_CONCURRENT_REQUESTS // 2
    timeout: float = 30.0
    keepalive_expiry: float = 5.0
    connect_timeout: float = 10.0
    retries: int = 3

class TicketingClientFactory:
    """Factory for creating ticketing system clients with connection pooling."""
    
    def __init__(self, config: TicketingConfig = TicketingConfig()):
        self._clients: Dict[TicketingSystemType, Type[BaseTicketingClient]] = {
            TicketingSystemType.JIRA: JiraClient,
            TicketingSystemType.AZURE: AzureClient
        }
        self._http_clients: Dict[TicketingSystemType, httpx.AsyncClient] = {}
        self._transport = httpx.AsyncHTTPTransport(
            limits=Limits(
                max_connections=config.max_connections,
                max_keepalive_connections=config.max_keepalive_connections,
                keepalive_expiry=config.keepalive_expiry
            ),
            retries=config.retries
        )
        self._timeout = Timeout(
            config.timeout,
            connect=config.connect_timeout,
            read=config.timeout,
            write=config.timeout
        )

    def _create_client(self, service_type: TicketingSystemType) -> httpx.AsyncClient:
        """Create a new HTTP client for a specific service type."""
        return httpx.AsyncClient(
            timeout=self._timeout,
            transport=self._transport,
            http2=True,
            follow_redirects=True
        )

    def get_http_client(self, service_type: TicketingSystemType) -> httpx.AsyncClient:
        """Get or create an HTTP client for a specific service type."""
        if service_type not in self._http_clients or self._http_clients[service_type].is_closed:
            self._http_clients[service_type] = self._create_client(service_type)
        return self._http_clients[service_type]
        
    def get_client(self, api_key: APIKeySchema) -> BaseTicketingClient:
        """Get a client instance for the specified ticketing system."""
        client_class = self._clients.get(api_key.service_type)
        if not client_class:
            raise ValueError(f"Unsupported ticketing system type: {api_key.service_type}")
        
        http_client = self.get_http_client(api_key.service_type)
        return client_class(http_client)

    async def cleanup(self):
        """Cleanup all HTTP clients when shutting down."""
        if self._http_clients:
            await asyncio.gather(
                *[client.aclose() for client in self._http_clients.values() if not client.is_closed]
            )
            self._http_clients.clear() 