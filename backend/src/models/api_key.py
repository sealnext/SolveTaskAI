from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .associations import api_key_project_association
from config.enums import TicketingSystemType

class APIKeyDB(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    api_key = Column(String(512), nullable=False, unique=True)
    service_type = Column(Enum(TicketingSystemType), nullable=False)
    domain = Column(String(255), nullable=False)
    domain_email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    permissions = Column(Text, nullable=True)

    # Relationships
    user = relationship("UserDB", back_populates="api_keys")
    projects = relationship("ProjectDB", secondary=api_key_project_association, back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, api_key={self.api_key})>"
