from typing import Literal
from pydantic import BaseModel, Field
from agent.state import AgentState

class TicketToolInput(BaseModel):
    """Schema for ticket tool input."""
    detailed_query: str = Field(
        description="Detailed description of what to do with the ticket"
    )
    state: AgentState = Field(
        description="The current state of the agent"
    )

class RetrieveToolInput(BaseModel):
    """Schema for retrieve tool input."""
    query: str = Field(
        description="The search query to use for document retrieval"
    )