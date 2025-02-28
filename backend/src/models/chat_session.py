from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(String, primary_key=True)  # UUID as string
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    messages = Column(JSON, nullable=False, default=list)  # Store messages as JSON
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("UserDB", back_populates="chat_sessions")
    project = relationship("ProjectDB", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, project_id={self.project_id})>"