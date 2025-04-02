from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schema.api_key import APIKey


class DocumentEmbedding(BaseModel):
    ticket_url: str
    issue_type: str
    status: str
    priority: str
    sprint: Optional[str]
    key: str
    labels: List[str]
    resolution: Optional[str]
    parent: Optional[str]
    assignee: Optional[str]
    reporter: str
    resolutiondate: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    embedding_vector: str


class DocumentEmbeddingCreate(BaseModel):
    project_id: int
    project_key: str
    domain: str
    external_id: str
    api_key: Optional[APIKey] = None
    action: str = "add"  # "add" or "delete"
