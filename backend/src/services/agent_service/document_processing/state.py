from typing import List, TypedDict, Literal
from models.apikey import APIKey
from schemas import Ticket
from models import Project

class AgentState(TypedDict):
    project: Project
    api_key: APIKey
    tickets: List[Ticket]
    status: str
    action: Literal['delete', 'add']
