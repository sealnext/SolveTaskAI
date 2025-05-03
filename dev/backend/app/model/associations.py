from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table

from app.model.base import Base

api_key_project_association = Table(
	'api_key_project',
	Base.metadata,
	Column('api_key_id', Integer, ForeignKey('api_keys.id'), primary_key=True),
	Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
)

user_project_association = Table(
	'user_project',
	Base.metadata,
	Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
	Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
)


thread_user_association = Table(
	'thread_user',
	Base.metadata,
	Column('thread_id', String, primary_key=True),
	Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
	Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
	Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
	Column(
		'updated_at',
		DateTime(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
	),
)
