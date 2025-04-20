from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.associations import user_project_association
from app.model.base import Base, utc_now

if TYPE_CHECKING:
	from app.model.api_key import ApiKeyDB
	from app.model.project import ProjectDB


class UserDB(Base):
	__tablename__ = 'users'

	id: Mapped[int] = mapped_column(init=False, primary_key=True)
	name: Mapped[str] = mapped_column()
	email: Mapped[str] = mapped_column(String(50), index=True, unique=True)
	github_id: Mapped[str | None] = mapped_column(index=True, unique=True, default=None)
	google_id: Mapped[str | None] = mapped_column(index=True, unique=True, default=None)
	hashed_password: Mapped[str | None] = mapped_column(String(100), default=None)
	created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default_factory=utc_now)
	updated_at: Mapped[datetime | None] = mapped_column(
		TIMESTAMP(timezone=True), default=None, onupdate=utc_now
	)
	last_seen: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), default=None)

	# One-to-many relationship to API keys
	api_keys: Mapped[List['ApiKeyDB']] = relationship(
		back_populates='user', cascade='all, delete-orphan', default_factory=list
	)

	# Many-to-many relationship with projects
	projects: Mapped[List['ProjectDB']] = relationship(
		secondary=user_project_association, back_populates='users', default_factory=list
	)
