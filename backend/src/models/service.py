from sqlalchemy import Column, Integer, Enum
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum as PyEnum

from .base import Base

class ServiceType(PyEnum):
    JIRA = "jira"
    AZURE = "azure"

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(Enum(ServiceType), nullable=False)

    # Relationship to Projects (One-to-many)
    projects = relationship("Project", back_populates="service")

    def __repr__(self):
        return f"<Service(id={self.id}, service_name={self.service_name.value})>"
