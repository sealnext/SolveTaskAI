from sqlalchemy import Column, Integer, String, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from .base import Base
from config.enums import TicketingSystemType
from .associations import api_key_project

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    name = Column(String, index=True)
    domain = Column(String(255), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="projects")
    api_keys = relationship("APIKey", secondary=api_key_project, back_populates="projects")
    embeddings = relationship("Embedding", back_populates="project")

    __table_args__ = (
        Index('ix_projects_company_service', 'company_id'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, company_id={self.company_id})>"
