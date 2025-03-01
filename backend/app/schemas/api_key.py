from app.models.api_key import APIKeyDB
from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl
from app.config.enums import TicketingSystemType


class APIKey(BaseModel):
    service_type: TicketingSystemType = Field(
        ..., description="Type of the ticketing system"
    )
    api_key: str = Field(
        ..., min_length=1, description="API key for the ticketing system"
    )
    domain: str = Field(..., description="Domain URL for the ticketing system")
    domain_email: EmailStr = Field(
        ..., description="Email address associated with the domain"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_type": "JIRA",
                "api_key": "abc123",
                "domain": "https://example.atlassian.net",
                "domain_email": "admin@example.com",
            }
        }

    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate and normalize domain URL.

        Ensures:
        1. Domain starts with https://
        2. Domain doesn't end with /
        """
        # Add https:// if not present
        if not v.startswith("https://"):
            v = "https://" + v.removeprefix("http://")

        # Remove trailing slash
        v = v.rstrip("/")

        try:
            AnyHttpUrl(v)
        except ValueError:
            raise ValueError("Invalid domain URL")
        return v

    def model_post_init(self, __context):
        self.domain = self.validate_domain(self.domain)

    @classmethod
    def from_orm(cls, obj: APIKeyDB):
        """Convert APIKey model to APIKeySchema."""
        return cls(
            service_type=obj.service_type,
            api_key=obj.api_key,
            domain=obj.domain,
            domain_email=obj.domain_email,
        )


class APIKeyResponse(BaseModel):
    id: int
    service_type: TicketingSystemType
    domain: str
    domain_email: EmailStr

    class Config:
        from_attributes = True


class APIKeyCreate(APIKey):
    pass
