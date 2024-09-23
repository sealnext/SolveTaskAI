from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime, UTC
from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def is_active(self) -> bool:
        return datetime.now(UTC) < self.expires_at
