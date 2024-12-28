from typing import Literal
from pydantic import BaseModel, Field

class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    action: Literal["edit", "create", "delete"] = Field(
        description="The action to perform on the ticket"
    )
    detailed_query: str = Field(
        description="Detailed description of what to do with the ticket"
    )
    ticket_id: str = Field(
        description="The ID of the ticket (required for edit and delete actions)"
    )

class RetrieveToolInput(BaseModel):
    """Schema for retrieve tool input."""
    query: str = Field(
        description="The search query to use for document retrieval"
    )