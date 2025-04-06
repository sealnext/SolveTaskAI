from pydantic import BaseModel, ConfigDict, model_validator

from app.service.ticketing.enums import TicketingSystemType


class ProjectBase(BaseModel):
	model_config = ConfigDict(from_attributes=True)


class ExternalProject(ProjectBase):
	"""Schema for external project data. JIRA only for now."""

	name: str
	key: str
	id: str
	avatarUrl: str

	@model_validator(mode='before')
	@classmethod
	def extract_avatar_url(cls, data: dict) -> dict:
		"""Extract the smallest avatar URL from avatarUrls with fallbacks."""
		if isinstance(data, dict):
			avatar_urls = data.get('avatarUrls', {})

			data['avatarUrl'] = (
				avatar_urls.get('16x16')
				or avatar_urls.get('24x24')
				or avatar_urls.get('32x32')
				or avatar_urls.get('48x48')
				or ''
			)
		return data


class ProjectCreate(ProjectBase):
	name: str
	domain: str
	service_type: TicketingSystemType
	key: str
	api_key_id: int
	external_id: str


class Project(ProjectBase):
	id: int
	name: str
	domain: str
	service_type: TicketingSystemType
	key: str
	external_id: int


class ProjectResponse(ProjectBase):
	id: int
	name: str
