from typing import Annotated, TypedDict, List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
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
    
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("retry_retrieval", retry_retrieve_documents)
    workflow.add_node("grade_documents", grade_documents)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("retry_retrieval", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "retry": "retry_retrieval",
            "generate": END,
            "max retries": END
        }
    )

    graph = workflow.compile()
    logger.debug(f"Compiled graph nodes: {graph.nodes}")
    return graph

class RetrieveInput(BaseModel):
    """Input for the RetrieveDocuments tool."""
    question: str = Field(
        ...,
        description="The question to search documents for"
    )

class RetrieveDocuments(BaseModel):
    """Tool for retrieving relevant documents from the project's knowledge base."""
    name: str = "RetrieveDocuments"
    description: str = "Retrieves relevant documents from the project's knowledge base to answer the user's question"
    project: Any
    api_key: Any

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def to_tool(self) -> Dict:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to search documents for"
                        }
                    },
                    "required": ["question"]
                }
            }
        }

    async def invoke(self, question: str) -> List[dict]:
        """Execute the retrieve workflow."""
        logger.info(f"Retrieving documents for question: {question}")
        
        state = {
            "question": question,
            "project": self.project,
            "api_key": self.api_key,
            "documents": [],
            "retry_retrieve_count": 0,
            "ignore_tickets": [],
            "messages": [],
            "max_retries": 3,
            "answers": 0,
            "loop_step": 0,
            "tickets": [],
            "status": "started"
        }
        
        workflow = create_retrieve_workflow()
        result = await workflow.ainvoke(state)
        
        if result and isinstance(result, dict):
            return result.get("documents", [])
        return []