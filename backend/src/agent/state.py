"""State management

This module defines the state structures used in the graph.
"""

from dataclasses import dataclass
from typing import Annotated, Sequence, TypeVar
from functools import partial

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

def add_unique_documents(
    current_documents: Sequence[Document],
    new_documents: Sequence[Document],
) -> list[Document]:
    """Custom reducer that adds documents using set operations."""
    return list(set(current_documents) | set(new_documents))

@dataclass
class AgentState:
    messages: Annotated[list[AnyMessage], add_messages]
    documents: Annotated[list[Document], partial(add_unique_documents)]