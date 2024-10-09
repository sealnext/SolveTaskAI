from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship

from .base import Base
from services.data_extractor.data_extractor import TicketingSystemType

class ServiceType(PyEnum):
    JIRA = "jira"
    AZURE = "azure"

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ticketing_system_type = Column(Enum(TicketingSystemType), nullable=False)
    jira_url = Column(String, nullable=True)
    azure_url = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    service_type = Column(Enum(ServiceType), nullable=False)
    domain = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="projects")
    api_keys = relationship("APIKey", back_populates="project")

    __table_args__ = (
        Index('ix_projects_company_service', 'company_id', 'service_type'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, project_name={self.project_name}, company_id={self.company_id}, service_type={self.service_type})>"
