"""State management

This module defines the state structures used in the graph.
"""

from typing import Annotated, Sequence, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel

from models import Project
from schemas import APIKeySchema

def add_unique_documents(
    current_documents: Sequence[Document],
    new_documents: Sequence[Document],
) -> list[Document]:
    """Custom reducer that adds documents using set operations."""
    return list(set(current_documents) | set(new_documents))


class AgentState(BaseModel):
    messages: Annotated[Sequence[AnyMessage], add_messages] = []
    documents: Annotated[Sequence[Document], add_unique_documents] = []
    project_data: Optional[Dict[str, Any]] = None  # Va conține datele serializate din Project
    api_key: Optional[APIKeySchema] = None
    
    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True
    }