from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import api_key_project_association
from app.model.base import Base, utc_now
from app.service.ticketing.enums import TicketingSystemType

if TYPE_CHECKING:
	from app.model.project import ProjectDB
	from app.model.user import UserDB


class ApiKeyDB(Base):
	__tablename__ = 'api_keys'

	id: Mapped[int] = mapped_column(init=False, primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
	api_key: Mapped[str] = mapped_column(String(512), unique=True)
	service_type: Mapped[TicketingSystemType] = mapped_column()
	domain: Mapped[str] = mapped_column()
	domain_email: Mapped[str] = mapped_column()

	# One-to-many relationship to UserDB
	user: Mapped['UserDB'] = relationship(back_populates='api_keys')

	created_at: Mapped[datetime] = mapped_column(default_factory=utc_now)
	expires_at: Mapped[datetime] = mapped_column(
		default_factory=lambda: utc_now() + timedelta(days=1)
	)

	# Many-to-many relationship to ProjectDB
	projects: Mapped[List['ProjectDB']] = relationship(
		secondary=api_key_project_association, back_populates='api_keys', default_factory=list
	)

	def __repr__(self):
		return f'<APIKey(id={self.id!r}, user_id={self.user_id!r}, api_key={self.api_key!r})>'
