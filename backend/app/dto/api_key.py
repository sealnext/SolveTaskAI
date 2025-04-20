from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.service.ticketing.enums import TicketingSystemType


class ApiKey(BaseModel):
	id: int | None = Field(None, description='Unique identifier for the API key')
	service_type: TicketingSystemType = Field(..., description='Type of the ticketing system')
	api_key: str = Field(..., min_length=1, description='API key for the ticketing system')
	domain: str = Field(..., description='Domain URL for the ticketing system')
	domain_email: EmailStr = Field(..., description='Email address associated with the domain')
	expires_at: datetime | None = Field(
		None, description='Optional expiration timestamp for the API key'
	)

	model_config = ConfigDict(from_attributes=True)

	@field_validator('domain', mode='before')
	@classmethod
	def normalize_domain(cls, v: str) -> str:
		# Add https:// if not present
		if not v.startswith('https://'):
			v = 'https://' + v.removeprefix('http://')

		# Remove trailing slash
		v = v.rstrip('/')

		try:
			AnyHttpUrl(v)
		except ValueError:
			raise ValueError('Invalid domain URL')
		return v


class ApiKeyResponse(BaseModel):
	id: int
	service_type: TicketingSystemType
	domain: str
	domain_email: EmailStr
	api_key: str = Field(..., description='Masked API key')

	@field_validator('api_key', mode='before')
	@classmethod
	def mask_api_key(cls, value: str) -> str:
		if value:
			return f'{value[:3]}{"*" * 5}'
		return value

	model_config = ConfigDict(from_attributes=True)


class ApiKeyCreate(BaseModel):
	service_type: TicketingSystemType = Field(..., description='Type of the ticketing system')
	api_key: str = Field(..., min_length=1, description='API key for the ticketing system')
	domain: str = Field(..., description='Domain URL for the ticketing system')
	domain_email: EmailStr = Field(..., description='Email address associated with the domain')

	model_config = ConfigDict(from_attributes=True)

	@field_validator('domain', mode='before')
	@classmethod
	def validate_domain(cls, v: str) -> str:
		return ApiKey.normalize_domain(v)
