from fastapi import Depends
from dependencies import get_project_repository, get_api_key_repository
from repositories import ProjectRepository, APIKeyRepository
from .document_processing_graph import create_document_processing_graph
from .self_rag_graph import create_self_rag_graph

__all__ = ["process_documents", "perform_self_rag"]

__version__ = "0.1.0"

async def process_documents(input_data: dict):
    graph = create_document_processing_graph()
    result = await graph.ainvoke(input_data)
    return result

async def perform_self_rag(input_data: dict):
    result = await self_rag_graph.ainvoke(input_data)
    return result
