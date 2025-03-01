from typing import List, TypedDict, Literal
from app.schemas.ticket import Ticket
from app.models.project import ProjectDB
from app.schemas.api_key import APIKey


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
    action: Literal["delete", "add"]
    retry_retrieve_count: int
    retry_retrieve: bool
    ignore_tickets: List[str]
