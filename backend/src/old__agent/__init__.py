
from .agent import Agent
import logging

__all__ = ["process_documents", "Agent"]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

async def process_documents(agent_state):
    graph = create_document_processing_graph()
    logger.debug(f"Graph nodes before invocation: {graph.nodes}")
    result = await graph.ainvoke(agent_state)
    return result
