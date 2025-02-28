from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from config import VECTOR_DIMENSION
from .base import Base

class Embedding(Base):
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True, index=True)
    ticket_url = Column(String(512), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    embedding_vector = Column(Vector(VECTOR_DIMENSION), nullable=False)
    issue_type = Column(String(128), nullable=False)
    status = Column(String(128), nullable=False)
    priority = Column(String(128), nullable=False)
    sprint = Column(String(128), nullable=True)
    key = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to Projects (Many-to-one)
    project = relationship("ProjectDB", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, ticket_url={self.ticket_url})>"