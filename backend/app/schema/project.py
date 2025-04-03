from pydantic import BaseModel, ConfigDict, model_validator

from app.service.ticketing.enums import TicketingSystemType


class ExternalProject(BaseModel):
	"""Schema for external project data."""

	name: str
	key: str
	id: str
	avatarUrl: str
	projectTypeKey: str
	style: str

	model_config = {
		'from_attributes': True,
		'populate_by_name': True,
		'extra': 'allow',
		'arbitrary_types_allowed': True,
	}

	@model_validator(mode='before')
	@classmethod
	def extract_avatar_url(cls, data: dict) -> dict:
		"""Extract the 16x16 avatar URL from avatarUrls."""
		if isinstance(data, dict):
			avatar_urls = data.get('avatarUrls', {})
			data['avatarUrl'] = avatar_urls.get('16x16', '')
		return data


class Project(BaseModel):
	id: int
	name: str
	domain: str
	service_type: TicketingSystemType
	key: str
	external_id: int

	model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
	name: str | None = None
	domain: str | None = None


class ProjectCreate(BaseModel):
	name: str
	domain: str
	service_type: TicketingSystemType
	key: str
	api_key_id: int
	external_id: int

	class Config:
		from_attributes = True
