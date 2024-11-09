from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
import logging
from .state import AgentState
from .nodes import retrieve_documents, retry_retrieve_documents, grade_documents
from .edges import decide_after_grading
from models import Project
from models.apikey import APIKey

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

class RetrieveDocuments:
    def __init__(self, project, api_key):
        self.project = project
        self.api_key = api_key

    def to_tool(self):
        """Convert the retriever to a LangChain tool."""
        @tool
        async def retrieve_documents(query: str) -> str:
            """
            Retrieve relevant documents based on the query.
            
            Args:
                query: The search query to use for document retrieval
            
            Returns:
                String containing the retrieved documents or empty if none found
            """
            logger.info(f"Retrieving documents for query: {query}")
            
            try:
                documents = await self.invoke(query)
                if not documents:
                    return ""
                
                formatted_docs = [
                    f"Document {i+1}:\n{doc.page_content}\nMetadata: {doc.metadata}"
                    for i, doc in enumerate(documents)
                ]
                return "\n\n".join(formatted_docs)
            except Exception as e:
                logger.error(f"Error in retrieve_documents: {e}", exc_info=True)
                return f"Error retrieving documents: {str(e)}"
            
        return retrieve_documents

    async def invoke(self, query: str):
        """Execute the retrieve workflow."""
        try:
            state = {
                "question": query,
                "project": self.project,
                "api_key": self.api_key,
                "documents": [],
                "retry_retrieve_count": 0,
                "ignore_tickets": [],
                "messages": [],
                "max_retries": 3,
                "status": "started"
            }
            
            workflow = create_retrieve_workflow()
            result = await workflow.ainvoke(state)
            
            if result and isinstance(result, dict):
                return result.get("documents", [])
            return []
        except Exception as e:
            logger.error(f"Error in invoke: {e}", exc_info=True)
            raise