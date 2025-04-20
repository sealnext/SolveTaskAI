from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import (
	api_key_project_association,
	user_project_association,
)
from app.model.base import Base
from app.service.ticketing.enums import TicketingSystemType

if TYPE_CHECKING:
	from app.model.api_key import ApiKeyDB
	from app.model.user import UserDB


class ProjectDB(Base):
	__tablename__ = 'projects'

	id: Mapped[int] = mapped_column(init=False, primary_key=True)
	name: Mapped[str] = mapped_column()
	domain: Mapped[str] = mapped_column()
	service_type: Mapped[TicketingSystemType] = mapped_column()
	key: Mapped[str] = mapped_column()
	external_id: Mapped[str] = mapped_column(unique=True)

	# Many-to-many relationship to ApiKeyDB
	api_keys: Mapped[List['ApiKeyDB']] = relationship(
		secondary=api_key_project_association, back_populates='projects', default_factory=list
	)

	# Many-to-many relationship to UserDB
	users: Mapped[List['UserDB']] = relationship(
		secondary=user_project_association, back_populates='projects', default_factory=list
	)

	def __repr__(self):
		return f'<Project(id={self.id!r}, name={self.name!r})>'
