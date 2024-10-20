from langgraph.graph import StateGraph, END
from .nodes import access_documents_with_api_key, generate_embeddings
from .state import AgentState
from typing import Dict, Any

def create_document_processing_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("access_documents", access_documents_with_api_key)
    workflow.add_node("generate_embeddings", generate_embeddings)
    
    workflow.set_entry_point("access_documents")
    workflow.add_edge("access_documents", "generate_embeddings")
    workflow.add_edge("generate_embeddings", END)
    
    graph = workflow.compile()
    return graph
