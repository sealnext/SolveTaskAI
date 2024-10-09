from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)

    # Relationship to Projects (One-to-many)
    projects = relationship("Project", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, company_name={self.company_name})>"
