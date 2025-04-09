from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.dto.api_key import APIKey


class DocumentEmbedding(BaseModel):
	ticket_url: str
	issue_type: str
	status: str
	priority: str
	sprint: str | None
	key: str
	labels: List[str]
	resolution: str | None
	parent: str | None
	assignee: str | None
	reporter: str
	resolutiondate: datetime | None
	created_at: datetime
	updated_at: datetime
	embedding_vector: str


class DocumentEmbeddingCreate(BaseModel):
	project_id: int
	project_key: str
	domain: str
	external_id: str
	api_key: APIKey | None = None
	action: str = 'add'  # "add" or "delete"
