from models import APIKey
from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl
from config.enums import TicketingSystemType

class APIKeySchema(BaseModel):
    service_type: TicketingSystemType = Field(..., description="Type of the ticketing system")
    api_key: str = Field(..., min_length=1, description="API key for the ticketing system")
    domain: str = Field(..., description="Domain URL for the ticketing system")
    domain_email: EmailStr = Field(..., description="Email address associated with the domain")

    class Config:
        json_schema_extra = {
            "example": {
                "service_type": "JIRA",
                "api_key": "abc123",
                "domain": "https://example.atlassian.net",
                "domain_email": "admin@example.com"
            }
        }

    @classmethod
    def validate_domain(cls, v: str) -> str:
        try:
            AnyHttpUrl(v)
        except ValueError:
            raise ValueError("Invalid domain URL")
        return v

    def model_post_init(self, __context):
        self.domain = self.validate_domain(self.domain)
        
    @classmethod
    def from_orm(cls, obj: APIKey):
        """Convert APIKey model to APIKeySchema."""
        return cls(
            service_type=obj.service_type,
            api_key=obj.api_key,
            domain=obj.domain,
            domain_email=obj.domain_email
        )

class APIKeyResponse(BaseModel):
    id: int
    service_type: TicketingSystemType
    domain: str
    domain_email: EmailStr

    class Config:
        from_attributes = True
        
class APIKeyCreate(APIKeySchema):
    pass
