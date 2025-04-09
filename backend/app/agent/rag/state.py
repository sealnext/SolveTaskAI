from typing import List, Literal, TypedDict

from app.dto.api_key import APIKey
from app.dto.ticket import Ticket
from app.model.project import ProjectDB


class AgentState(TypedDict):
	question: str
	user_id: int
	project: ProjectDB
	api_key: APIKey
	generation: str
	max_retries: int
	answers: int
	loop_step: int
	documents: List[str]
	tickets: List[Ticket]
	status: str
	action: Literal['delete', 'add']
	retry_retrieve_count: int
	retry_retrieve: bool
	ignore_tickets: List[str]
