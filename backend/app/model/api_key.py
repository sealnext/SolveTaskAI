from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import api_key_project_association
from app.model.base import Base, utc_now
from app.service.ticketing.enums import TicketingSystemType


class APIKeyDB(Base):
	__tablename__ = 'api_keys'

	id: Mapped[int] = mapped_column(init=False, primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
	api_key: Mapped[str] = mapped_column(String(512), unique=True)
	service_type: Mapped[TicketingSystemType] = mapped_column()
	domain: Mapped[str] = mapped_column()
	domain_email: Mapped[str] = mapped_column()
	created_at: Mapped[datetime] = mapped_column(default_factory=utc_now)
	expires_at: Mapped[datetime] = mapped_column(
		default_factory=lambda: utc_now() + timedelta(days=1)
	)

	# Relationships
	user = relationship('UserDB', back_populates='api_keys')
	projects = relationship(
		'ProjectDB', secondary=api_key_project_association, back_populates='api_keys'
	)

	def __repr__(self):
		return f'<APIKey(id={self.id!r}, user_id={self.user_id!r}, api_key={self.api_key!r})>'
