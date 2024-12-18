"""State management

This module defines the state structures used in the graph.
"""

from dataclasses import dataclass, field
from typing import Annotated, Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from dataclasses import dataclass, field
from typing import List, Any



@dataclass
class AgentState():
    messages: Annotated[list[AnyMessage], add_messages]