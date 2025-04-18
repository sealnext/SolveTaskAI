from enum import Enum
from typing import Annotated, Any, Dict, Literal, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

class TicketAgentState(BaseModel):
	"""State for the ticket agent."""

	messages: Annotated[Sequence[AnyMessage], add_messages]
	internal_messages: Annotated[Sequence[AnyMessage], add_messages]

	review_config: Dict[str, Any] | None = None
	needs_review: bool = False
	done: bool = False
	retry_count: int = 0


class ReviewAction(str, Enum):
	"""Available review actions based on operation type."""

	CONFIRM = 'confirm'  # Proceed with operation as is
	CANCEL = 'cancel'  # Cancel the entire operation

class ReviewConfig(TypedDict):
	"""Configuration for review workflows."""

	question: str
	operation_type: Literal['edit', 'delete', 'create']
	available_actions: list[ReviewAction]
	expected_payload_schema: dict | None
	preview_data: dict | None
	metadata: dict
	operation_type: dict


class JiraTicketUpdate(BaseModel):
	"""Pydantic model for Jira ticket update."""

	fields: dict[str, Any]
	update: dict[str, Any]
