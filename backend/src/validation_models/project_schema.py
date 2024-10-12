from pydantic import BaseModel, Field
from typing import List, Optional
from config.enums import TicketingSystemType
class ExternalProjectSchema(BaseModel):
    name: str
    key: str
    id: str
    avatar_url: str = Field(alias="avatarUrl")
    project_type_key: str = Field(alias="projectTypeKey")
    style: str

    class Config:
        populate_by_name = True
        
class InternalProjectSchema(BaseModel):
    id: int
    name: str
    domain: str
    company_id: int
    service_type: TicketingSystemType

    class Config:
        from_attributes = True
    
class ProjectBase(BaseModel):
    name: str
    domain: str

class ProjectCreate(ProjectBase):
    company_id: int

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None

class ProjectInDB(ExternalProjectSchema):
    api_keys: List[str] = []
    embeddings: List[int] = []

class ProjectWithRelated(ProjectInDB):
    company: dict
