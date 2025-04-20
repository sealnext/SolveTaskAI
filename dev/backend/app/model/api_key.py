from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import api_key_project_association
from app.model.base import Base, utc_now
from app.service.ticketing.enums import TicketingSystemType
from sqlalchemy.sql.sqltypes import TIMESTAMP

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

	# Many-to-one relationship with UserDB
	user: Mapped['UserDB'] = relationship(back_populates='api_keys', init=False)

	created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default_factory=utc_now)

	# Many-to-many relationship to ProjectDB
	projects: Mapped[List['ProjectDB']] = relationship(
		secondary=api_key_project_association, back_populates='api_keys', default_factory=list
	)

	def __repr__(self):
		return f'<APIKey(id={self.id!r}, user_id={self.user_id!r}, api_key={self.api_key!r})>'
