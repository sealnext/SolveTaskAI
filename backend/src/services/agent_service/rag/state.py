from typing import List, TypedDict, Literal
from models.apikey import APIKey
from schemas import Ticket
from models import Project

class AgentState(TypedDict):
    question: str
    user_id: int
    project: Project
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
