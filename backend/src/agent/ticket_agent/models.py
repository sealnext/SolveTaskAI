from typing import Literal
from pydantic import BaseModel, Field
from typing import Annotated, Sequence, Any, Optional, Dict, Any, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from enum import Enum

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
    
class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    action: Literal["edit", "create", "delete"] = Field(description="The action to perform on the ticket")
    detailed_query: str = Field(description="Detailed description of what needs to be done")
    ticket_id: str = Field(description="The ID of the ticket to operate on")

class TicketAgentState(BaseModel):
    """State for the ticket agent."""
    messages: Annotated[Sequence[AnyMessage], add_messages]
    internal_messages: Annotated[Sequence[AnyMessage], add_messages]

    review_config: Optional[Dict[str, Any]] = None
    needs_review: bool = False
    done: bool = False
    retry_count: int = 0

class ReviewAction(str, Enum):
    """Available review actions based on operation type."""
    # Common actions
    CONFIRM = "confirm"  # Proceed with operation as is
    CANCEL = "cancel"      # Cancel the entire operation

    # Edit specific
    UPDATE_FIELDS = "update_fields"     # Update specific fields
    MODIFY_CHANGES = "modify_changes"   # Modify the proposed changes

    # Delete specific
    ARCHIVE_INSTEAD = "archive_instead" # Archive instead of delete
    SOFT_DELETE = "soft_delete"        # Soft delete option

class ReviewConfig(TypedDict):
    """Configuration for review workflows."""
    question: str
    operation_type: Literal["edit", "delete", "create"]
    available_actions: list[ReviewAction]
    expected_payload_schema: Optional[dict]
    preview_data: Optional[dict]
    metadata: dict
    operation_type: dict

class JiraTicketUpdate(BaseModel):
    """Pydantic model for Jira ticket update."""
    fields: dict[str, Any]
    update: dict[str, Any]