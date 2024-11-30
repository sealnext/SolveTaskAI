from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class IssueTypeSelectionSchema(BaseModel):
    """Schema for issue type selection response."""
    issue_type_id: str = Field(description="The ID of the selected issue type")
    reasoning: str = Field(description="Explanation of why this issue type was selected")

class FieldValueSchema(BaseModel):
    """Schema for field value collection."""
    field_values: Dict[str, Any] = Field(description="Values for ticket fields")
    missing_required: List[str] = Field(description="List of required fields still missing", default_list=[])
    suggested_optional: List[str] = Field(description="List of suggested optional fields", default_list=[])

class EditOperationSchema(BaseModel):
    """Schema for edit operations."""
    operation: str = Field(description="The type of edit operation (update/add/remove)")
    field: str = Field(description="The field to edit")
    value: Any = Field(description="The new value")
    reasoning: str = Field(description="Explanation of the edit") 