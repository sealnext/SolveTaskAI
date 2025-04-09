from logging import getLogger
from typing import AsyncIterator

from app.dto.api_key import APIKey
from app.dto.document_embeddings import DocumentEmbedding
from app.dto.ticket import JiraIssueSchema
from app.repository.document_embeddings_repository import DocumentEmbeddingsRepository
from app.service.ticketing.factory import TicketingClientFactory

logger = getLogger(__name__)


class DocumentEmbeddingsService:
	"""Service for managing document embeddings with optimized processing."""

	# Pre-allocate field order for consistent document structure
	FIELD_ORDER = ['summary', 'description', 'acceptance_criteria', 'comments']

	# Field separators for better semantic separation and context (embeddings)
	FIELD_SEPARATORS = {
		'summary': '\n### SUMMARY ###\n',
		'description': '\n### DESCRIPTION ###\n',
		'acceptance_criteria': '\n### ACCEPTANCE CRITERIA ###\n',
		'comments': '\n### COMMENTS ###\n',
	}

	# Batch size for processing
	BATCH_SIZE = 100

	def __init__(self, repository: DocumentEmbeddingsRepository, factory: TicketingClientFactory):
		"""Initialize with repository and ticketing client factory.

		Args:
		    repository: The DocumentEmbeddingsRepository instance
		    factory: The TicketingClientFactory instance for creating clients
		"""
		self.embeddings_repository = repository
		self.factory = factory
		logger.debug('Initialized DocumentEmbeddingsService')

	async def add_documents(
		self, domain: str, project_key: str, external_id: str, api_key: APIKey
	) -> None:
		"""
		Add documents from a ticketing system to the embeddings repository.
		Uses async generators and batching for optimal memory usage.

		Args:
		    domain: The ticketing system domain
		    project_key: The project key in the ticketing system
		    external_id: Internal identifier for the collection
		    api_key: The API key for ticketing system access
		"""
		logger.info(f'Adding documents for project {project_key}')

		# Get client from factory
		client = self.factory.get_client(api_key)

		# Get project details
		projects = await client.get_projects()
		project = next((p for p in projects if p.key == project_key), None)
		if not project:
			raise ValueError(f'Project {project_key} not found')

		# Create client with project
		client = self.factory.get_client(api_key, project)

		# Create async generator for documents
		async def document_generator():
			async for ticket in client.get_tickets():
				yield self._create_document_from_ticket(ticket)

		# Process documents
		await self.embeddings_repository.add_embeddings(
			domain=domain,
			project_key=project_key,
			external_id=external_id,
			documents=document_generator(),
		)

	def _create_document_from_ticket(self, ticket: JiraIssueSchema) -> DocumentEmbedding:
		"""Create a DocumentEmbedding from a ticket."""
		content_parts = []
		for field in self.FIELD_ORDER:
			value = getattr(ticket, field, None)
			if value:
				content_parts.append(f'{self.FIELD_SEPARATORS[field]}{value}')

		content = ''.join(content_parts)
		if not content.strip():
			raise ValueError(f'Empty content for ticket {ticket.key}')

		return DocumentEmbedding(
			embedding_vector=content,
			ticket_url=ticket.ticket_url,
			issue_type=ticket.issue_type,
			status=ticket.status,
			priority=ticket.priority,
			sprint=ticket.sprint,
			key=ticket.key,
			labels=ticket.labels,
			resolution=ticket.resolution,
			parent=ticket.parent,
			assignee=ticket.assignee,
			reporter=ticket.reporter,
			resolutiondate=ticket.resolutiondate,
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
		)

	async def delete_documents(self, domain: str, project_key: str, external_id: str) -> None:
		"""Delete all documents for a project from the embeddings repository."""
		logger.info(f'Deleting documents for project {project_key}')
		await self.embeddings_repository.delete_collection(
			domain=domain, project_key=project_key, external_id=external_id
		)
		logger.info(f'Successfully deleted collection for project {project_key}')

	async def _generate_documents(
		self, tickets_iterator: AsyncIterator[JiraIssueSchema]
	) -> AsyncIterator[DocumentEmbedding]:
		"""
		Generate document embeddings efficiently using batching and pre-allocation.

		Args:
		    tickets_iterator: Iterator of tickets from any supported system

		Yields:
		    DocumentEmbedding: Validated document embeddings
		"""
		# Pre-allocate content builder for reuse
		content_parts = []
		content_parts.extend([''] * len(self.FIELD_ORDER))

		async for ticket in tickets_iterator:
			try:
				# Fast validation of required fields
				if not (
					hasattr(ticket, 'key')
					and hasattr(ticket, 'summary')
					and ticket.key
					and ticket.summary
				):
					logger.warning(
						f'Skipping ticket with missing required fields: {getattr(ticket, "key", "unknown")}'
					)
					continue

				# Reset content parts (faster than creating new list)
				for i in range(len(content_parts)):
					content_parts[i] = ''

				# Build content efficiently
				for i, field in enumerate(self.FIELD_ORDER):
					value = getattr(ticket, field, None)
					if value:
						content_parts[i] = f'{self.FIELD_SEPARATORS[field]}{value}'

				# Join only non-empty parts
				content = ''.join(part for part in content_parts if part)

				# Skip if no content after joining
				if not content.strip():
					logger.warning(f'Skipping ticket {ticket.key} with empty content')
					continue

				# Create document with all available fields
				document = DocumentEmbedding(
					embedding_vector=content,
					ticket_url=ticket.ticket_url,
					issue_type=ticket.issue_type,
					status=ticket.status,
					priority=ticket.priority,
					sprint=ticket.sprint,
					key=ticket.key,
					labels=ticket.labels,
					resolution=ticket.resolution,
					parent=ticket.parent,
					assignee=ticket.assignee,
					reporter=ticket.reporter,
					resolutiondate=ticket.resolutiondate,
					created_at=ticket.created_at,
					updated_at=ticket.updated_at,
				)

				yield document

			except Exception as e:
				logger.error(
					f'Error creating document for ticket {getattr(ticket, "key", "unknown")}: {str(e)}'
				)
				continue
