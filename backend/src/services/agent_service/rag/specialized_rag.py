from typing import Annotated, TypedDict, List, Optional
from pydantic import BaseModel
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, END
from .nodes import retrieve_documents, retry_retrieve_documents, grade_documents
from .edges import decide_after_grading
from models import Project
from models.apikey import APIKey
import logging
from .state import AgentState

logger = logging.getLogger(__name__)

def create_retrieve_workflow():
    """Creates a specialized workflow for document retrieval."""
    logger.info("Creating retrieve workflow")
    
    workflow = StateGraph(AgentState)
    
    # Define the nodes - without generate
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("retry_retrieval", retry_retrieve_documents)
    workflow.add_node("grade_documents", grade_documents)

    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("retry_retrieval", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "retry": "retry_retrieval",
            "generate": END,  # Now ends after finding relevant documents
            "max retries": END
        }
    )

    # Compile the graph
    graph = workflow.compile()
    logger.debug(f"Compiled graph nodes: {graph.nodes}")
    return graph

class RetrieveDocuments(BaseModel):
    """Tool for retrieving relevant documents."""
    question: str = "The question to find relevant documents for"
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "question": "What are the key features of the latest release?"
                }
            ]
        }