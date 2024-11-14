from langgraph.graph import StateGraph, END
from .nodes import access_documents_with_api_key, generate_embeddings, delete_embeddings
from .state import AgentState
from .edge import route_action
import logging

logger = logging.getLogger(__name__)

def create_document_processing_graph():
    workflow = StateGraph(AgentState)
    
    workflow.set_conditional_entry_point(
        route_action,
        {
            "delete": "delete_embeddings",
            "add": "access_documents",
        },
    )
    
    # Nodes
    workflow.add_node("access_documents", access_documents_with_api_key)
    workflow.add_node("generate_embeddings", generate_embeddings)
    workflow.add_node("delete_embeddings", delete_embeddings)
    
    # Add edges
    workflow.add_edge("access_documents", "generate_embeddings")
    workflow.add_edge("generate_embeddings", END)
    workflow.add_edge("delete_embeddings", END)

    graph = workflow.compile()
    logger.debug(f"Compiled graph nodes: {graph.nodes}")
    return graph
