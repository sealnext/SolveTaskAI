import json
from textwrap import indent
from typing import Annotated, List, Optional, Dict, Any
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

async def execute_retrieve_workflow(query: str, project: Project, api_key: APIKey) -> List[Any]:
    """Execute the retrieve workflow with given parameters."""
    try:
        state = {
            "question": query,
            "project": project,
            "api_key": api_key,
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
        logger.error(f"Error in execute_retrieve_workflow: {e}", exc_info=True)
        raise

def create_retrieve_tool(project: Project, api_key: APIKey):
    """Creates a retrieve tool with project and api_key context."""
    
    @tool
    async def retrieve(query: str) -> str:
        """
        Use this tool for searching and retrieving information from tickets and documentation.
        ALWAYS use this tool for:
        - Finding information about bugs, issues, or features
        - Searching through ticket content
        - Getting context about specific topics
        - Answering questions about existing tickets
        - Finding how many tickets match certain criteria
        
        Do NOT use this tool for:
        - Creating new tickets
        - Updating existing tickets
        - Any actions that modify tickets
        - Questions about ability to modify tickets
        
        Args:
            query: The search query to use for document retrieval
        
        Returns:
            String containing the retrieved documents or empty if none found
        """
        
        logger.info(f"Tool retrieve called with query: {query}")
        
        try:
            documents = await execute_retrieve_workflow(query, project, api_key)
            if not documents:
                return ""
            
            formatted_docs = []
            for i, doc in enumerate(documents):
                doc_key = doc.metadata['ticket_url'].split('/')[-1]  # Extrage PZ-2 din URL
                
                doc_data = {
                    "metadata": doc.metadata,
                    "content": doc.page_content
                }
                doc_json = json.dumps(doc_data, indent=1)
                doc_str = f"Document {doc_key}:\n{indent(doc_json, '    ')}"
                formatted_docs.append(doc_str)
            return "\n\n".join(formatted_docs)
        except Exception as e:
            logger.error(f"Error in retrieve: {e}", exc_info=True)
            return f"Error retrieving documents: {str(e)}"
            
    return retrieve