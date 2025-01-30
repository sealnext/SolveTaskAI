from typing import Literal
from pydantic import BaseModel, Field

class FieldMapping(BaseModel):
    """Model for mapping fields from LLM to JIRA."""
    value: str = Field(description="The exact value to set for the field")
    confidence: Literal["High", "Medium", "Low"] = Field(description="Confidence level in the mapping")
    validation: Literal["Valid", "Needs Validation"] = Field(description="Whether the value needs user validation")

class TicketFieldMapping(BaseModel):
    """Model for all field mappings in a ticket."""
    mapped_fields: dict[str, FieldMapping] = Field(
        description="Dictionary mapping Jira field names to their corresponding values, confidence levels, and validation status"
    ) 