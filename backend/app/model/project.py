from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.model.associations import (
	api_key_project_association,
	user_project_association,
)
from app.model.base import Base
from app.service.ticketing.enums import TicketingSystemType


class ProjectDB(Base):
	__tablename__ = 'projects'

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, index=True)
	domain = Column(String(255), nullable=False)
	service_type = Column(Enum(TicketingSystemType), nullable=False)
	key = Column(String(255), nullable=False, unique=True)
	external_id = Column(String(255), nullable=False, unique=True)

	# Relationships
	api_keys = relationship(
		'APIKeyDB', secondary=api_key_project_association, back_populates='projects'
	)
	users = relationship('UserDB', secondary=user_project_association, back_populates='projects')
	chat_sessions = relationship('ChatSession', back_populates='project')

	def __repr__(self):
		return f'<Project(id={self.id}, name={self.name})>'
