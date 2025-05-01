import json
from datetime import datetime
from logging import getLogger
from textwrap import indent
from typing import Any, Dict, List

from langchain_core.documents import Document
from pydantic import BaseModel, RootModel, model_validator

logger = getLogger(__name__)


# Response models for Jira API
class AvatarUrls(BaseModel):
	"""Schema for avatar URLs."""

	model_config = {'extra': 'allow'}


class JiraProjectResponse(RootModel):
	"""Model for Jira project response."""

	root: List[dict]

	def dict(self, **kwargs) -> Dict[str, Any]:
		"""Convert list response to expected format."""
		return {'values': self.root}

	class Config:
		"""Allow direct list input."""

		frozen = True


class JiraSearchResponse(BaseModel):
	"""Model for Jira search response."""

	issues: List[dict]
	total: int

	class Config:
		"""Ensure response is always a dictionary."""

		frozen = True


class Ticket(BaseModel):
	ticket_api: str
	ticket_url: str
	issue_type: str | None = None
	status: str | None = None
	priority: str | None = None
	sprint: str | None = None
	embedding_vector: str | None = None
	labels: List[str] | None = None
	resolution: str | None = None
	parent: str | None = None
	assignee: str | None = None
	reporter: str | None = None
	resolutiondate: str | None = None
	created_at: str
	updated_at: str


class DocumentWrapper(BaseModel):
	metadata: Dict[str, Any]
	page_content: str

	@classmethod
	def from_langchain_doc(cls, doc: Document) -> 'DocumentWrapper':
		"""Create a document wrapper from a langchain Document"""

		# Keep all metadata fields and ensure they match our expected format
		metadata = {
			'ticket_url': doc.metadata.get('ticket_url', ''),
			'ticket_api': doc.metadata.get('key', ''),  # In RAG flow, 'key' is used for ticket_api
			'key': doc.metadata.get('key', ''),
			'labels': doc.metadata.get('labels', []),
			'parent': doc.metadata.get('parent'),
			'sprint': doc.metadata.get('sprint'),
			'status': doc.metadata.get('status'),
			'assignee': doc.metadata.get('assignee'),
			'priority': doc.metadata.get('priority'),
			'reporter': doc.metadata.get('reporter'),
			'issue_type': doc.metadata.get('issue_type'),
			'resolution': doc.metadata.get('resolution'),
			'resolutiondate': doc.metadata.get('resolutiondate'),
			'created_at': doc.metadata.get('created_at'),
			'updated_at': doc.metadata.get('updated_at'),
		}

		# Process page_content
		if isinstance(doc.page_content, str):
			content_dict = eval(doc.page_content)
			if isinstance(content_dict, dict):
				formatted_content = f"""Summary: {content_dict.get('summary', '')}
Description: {content_dict.get('description', '')}
Comments: {' '.join(content_dict.get('comments', []))}"""
				return cls(metadata=metadata, page_content=formatted_content)

		return cls(metadata=metadata, page_content=str(doc.page_content))

	def format_for_display(self) -> str:
		"""Format document for display in chat"""
		doc_key = self.metadata.get('ticket_url', '').split('/')[-1]
		doc_data = {'metadata': self.metadata, 'content': self.page_content}
		return f'Document {doc_key}:\n{indent(json.dumps(doc_data, indent=1), "    ")}'


class TicketContent(BaseModel):
	summary: str = ''
	description: str = ''
	comments: List[str] = []

	def __str__(self):
		return json.dumps(
			{
				'summary': self.summary,
				'description': self.description,
				'comments': self.comments,
			},
			indent=1,
		)

	def to_page_content(self) -> str:
		"""Convert ticket content to a formatted string for document representation"""
		return f"""Summary: {self.summary}
Description: {self.description}
Comments: {' '.join(self.comments)}"""


class JiraIssueContentSchema(BaseModel):
	content: TicketContent
	ticket_api: str
	ticket_url: str
	fields: Dict[str, Any] = {}

	class Config:
		populate_by_name = True

	@model_validator(mode='before')
	@classmethod
	def flatten_fields(cls, values):
		fields = values.get('fields', {}) or {}
		values['fields'] = fields

		api_self_url = values.get('self', '')
		base_url = '/'.join(api_self_url.split('/')[:3])
		ticket_key = values.get('key', None)
		values['ticket_url'] = f'{base_url}/browse/{ticket_key}'
		values['ticket_api'] = api_self_url

		summary = fields.get('summary') or 'No title provided'
		description = fields.get('description') or 'No description provided'

		comments = fields.get('comment', {}).get('comments', [])
		comments_list = (
			[
				f'{comment.get("author", {}).get("displayName", "Unknown")}: {comment.get("body", "")}'
				for comment in comments
			]
			if comments
			else []
		)

		values['content'] = {
			'summary': summary,
			'description': description,
			'comments': comments_list,
		}

		return values

	def __str__(self) -> str:
		"""Convert to minimal string representation with only non-empty fields."""
		result = {
			'ticket_url': self.ticket_url,
			'content': {
				k: v
				for k, v in self.content.__dict__.items()
				if v and (isinstance(v, str) and v.strip() or not isinstance(v, str))
			},
		}

		metadata = {}
		for field in ['status', 'priority', 'issue_type', 'assignee', 'reporter']:
			value = (
				self.fields.get(field, {}).get('name')
				if isinstance(self.fields.get(field), dict)
				else None
			)
			if value:
				metadata[field] = value

		if metadata:
			result['metadata'] = metadata

		return json.dumps(result, indent=2)


class JiraIssueSchema(BaseModel):
	"""Schema for Jira issue data."""

	key: str
	summary: str
	description: str | None = None
	issue_type: str | None = None
	status: str | None = None
	priority: str | None = None
	sprint: str | None = None
	labels: List[str] = []
	resolution: str | None = None
	parent: str | None = None
	assignee: str | None = None
	reporter: str | None = None
	resolutiondate: datetime | None = None
	created_at: datetime
	updated_at: datetime
	project_id: str
	ticket_url: str

	class Config:
		populate_by_name = True

	@model_validator(mode='before')
	@classmethod
	def flatten_fields(cls, values):
		fields = values.get('fields', {})

		# Extract base URLs and identifiers
		api_self_url = values.get('self', '')
		base_url = '/'.join(api_self_url.split('/')[:3])
		ticket_key = values.get('key', '')

		# Map fields
		values.update(
			{
				'key': values.get('key'),
				'summary': fields.get('summary'),
				'description': fields.get('description'),
				'issue_type': fields.get('issuetype', {}).get('name'),
				'status': fields.get('status', {}).get('name'),
				'priority': fields.get('priority', {}).get('name'),
				'sprint': fields.get('sprint', {}).get('name') if fields.get('sprint') else None,
				'labels': fields.get('labels', []),
				'resolution': fields.get('resolution', {}).get('name')
				if fields.get('resolution')
				else None,
				'parent': fields.get('parent', {}).get('key') if fields.get('parent') else None,
				'assignee': fields.get('assignee', {}).get('displayName')
				if fields.get('assignee')
				else None,
				'reporter': fields.get('reporter', {}).get('displayName')
				if fields.get('reporter')
				else None,
				'resolutiondate': fields.get('resolutiondate'),
				'created_at': fields.get('created'),
				'updated_at': fields.get('updated'),
				'ticket_url': f'{base_url}/browse/{ticket_key}',
			}
		)

		return values
