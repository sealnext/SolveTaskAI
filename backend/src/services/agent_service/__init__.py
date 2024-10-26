from .document_processing.graph import create_document_processing_graph
from .rag.graph import create_self_rag_graph
import logging

__all__ = ["process_documents", "perform_self_rag"]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

async def process_documents(agent_state):
    graph = create_document_processing_graph()
    logger.debug(f"Graph nodes before invocation: {graph.nodes}")
    result = await graph.ainvoke(agent_state)
    return result

async def perform_self_rag(agent_state):
    graph = create_self_rag_graph()
    result = await graph.ainvoke(agent_state)
    return result
