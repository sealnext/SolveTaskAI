from pydantic import BaseModel, Field
from typing import List, Optional
from config.enums import TicketingSystemType
from pydantic import model_validator

class ExternalProjectSchema(BaseModel):
    """Schema for external project data."""
    name: str
    key: str
    id: str
    avatarUrl: str
    projectTypeKey: str
    style: str

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "allow",
        "arbitrary_types_allowed": True
    }

    @model_validator(mode='before')
    @classmethod
    def extract_avatar_url(cls, data: dict) -> dict:
        """Extract the 16x16 avatar URL from avatarUrls."""
        if isinstance(data, dict):
            avatar_urls = data.get('avatarUrls', {})
            data['avatarUrl'] = avatar_urls.get('16x16', '')
        return data

class InternalProjectSchema(BaseModel):
    id: int
    name: str
    domain: str
    service_type: TicketingSystemType
    key: str
    internal_id: str

    class Config:
        from_attributes = True
    
class ProjectBase(BaseModel):
    name: str
    domain: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None

class ProjectInDB(ExternalProjectSchema):
    api_keys: List[str] = []
    embeddings: List[int] = []

class InternalProjectCreate(BaseModel):
    name: str
    domain: str
    service_type: TicketingSystemType
    key: str
    internal_id: str
    api_key_id: int

    class Config:
        from_attributes = True
