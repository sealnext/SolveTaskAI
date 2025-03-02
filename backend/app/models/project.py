from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.config.enums import TicketingSystemType
from app.models.associations import (
    api_key_project_association,
    user_project_association,
)
from app.models.embedding import Embedding


class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    domain = Column(String(255), nullable=False)
    service_type = Column(Enum(TicketingSystemType), nullable=False)
    key = Column(String(255), nullable=False, unique=True)
    internal_id = Column(String(255), nullable=False, unique=True)

    # Relationships
    api_keys = relationship(
        "APIKeyDB", secondary=api_key_project_association, back_populates="projects"
    )
    embeddings = relationship("Embedding", back_populates="project", lazy="selectin")
    users = relationship(
        "UserDB", secondary=user_project_association, back_populates="projects"
    )
    chat_sessions = relationship("ChatSession", back_populates="project")

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"
