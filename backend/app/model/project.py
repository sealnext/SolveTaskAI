from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import (
	api_key_project_association,
	user_project_association,
)
from app.model.base import Base
from app.service.ticketing.enums import TicketingSystemType


class ProjectDB(Base):
	__tablename__ = 'projects'

	id: Mapped[int] = mapped_column(init=False, primary_key=True)
	name: Mapped[str] = mapped_column()
	domain: Mapped[str] = mapped_column()
	service_type: Mapped[TicketingSystemType] = mapped_column()
	key: Mapped[str] = mapped_column()
	external_id: Mapped[str] = mapped_column(unique=True)

	# Relationships
	api_keys = relationship(
		'APIKeyDB', secondary=api_key_project_association, back_populates='projects'
	)
	users = relationship('UserDB', secondary=user_project_association, back_populates='projects')

	def __repr__(self):
		return f'<Project(id={self.id!r}, name={self.name!r})>'
