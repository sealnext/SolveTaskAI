from langgraph.graph import StateGraph, END
from .nodes import grade_documents, generate, retrieve_documents, retry_retrieve_documents
from .edges import decide_after_grading, grade_generation_hallucination_and_usefulness
from .state import AgentState
import logging

logger = logging.getLogger(__name__)

def create_self_rag_graph():
    workflow = StateGraph(AgentState)

    # Define the nodes 
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("retry_retrieve_with_alternatives", retry_retrieve_documents) 
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    
    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("retry_retrieve_with_alternatives", "grade_documents") 
    
    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "retry": "retry_retrieve_with_alternatives",
            "generate": "generate",
            "max retries": END,
        },
    )
    
    workflow.add_conditional_edges(
        "generate",
        grade_generation_hallucination_and_usefulness,
        {
            "useful": END,
            "not useful": "retrieve",
            "max retries": END,
        },
    )

    graph = workflow.compile()
    logger.debug(f"Compiled graph nodes: {graph.nodes}")
    return graph
