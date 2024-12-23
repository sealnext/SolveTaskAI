import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import HTTPException

from models.document_embeddings import DocumentEmbedding, DocumentEmbeddingCreate
from repositories.document_embeddings_repository import DocumentEmbeddingsRepository
from services.data_extractor.data_extractor_factory import create_data_extractor

logger = logging.getLogger(__name__)

class DocumentEmbeddingsService:
    def __init__(self, repository: DocumentEmbeddingsRepository):
        self.repository = repository
        logger.debug("Initialized DocumentEmbeddingsService")
    
    def _validate_request(self, request: DocumentEmbeddingCreate) -> None:
        """Validate the incoming request data."""
        if not all([request.project_id, request.project_key]):
            logger.error("Missing required request data")
            raise HTTPException(status_code=400, detail="Missing required request data")
        
        if request.action not in ["add", "delete"]:
            logger.error(f"Invalid action: {request.action}")
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'add' or 'delete'")
        
        if request.action == "add" and not request.api_key:
            logger.error("API key is required for add action")
            raise HTTPException(status_code=400, detail="API key is required for add action")
    
    async def process_documents(self, request: DocumentEmbeddingCreate) -> Dict[str, Any]:
        """Process documents based on the action (add/delete) specified in the request."""
        logger.debug(f"Processing documents for project {request.project_id} with action {request.action}")
        self._validate_request(request)
        
        try:
            if request.action == "delete":
                await self.repository.delete_collection(
                    domain=request.domain,
                    project_key=request.project_key,
                    internal_id=request.internal_id
                )
                return {"status": "success", "message": "Collection deleted successfully"}
            
            # For add action
            unique_identifier = self.repository._get_unique_identifier(
                request.domain,
                request.project_key,
                request.internal_id
            )
            
            # Check if collection exists
            if await self.repository.collection_exists(unique_identifier):
                domain_with_slash = request.domain if request.domain.endswith('/') else f"{request.domain}/"
                return {
                    "status": "exists",
                    "message": f"Collection for {domain_with_slash}browse/{request.project_key} already exists.",
                    "tickets": []
                }
            
            # Get tickets from data extractor using the complete API key object
            logger.info(f"Fetching tickets for project {request.project_id} using {request.api_key.service_type} API key")
            data_extractor = create_data_extractor(request.api_key)
            tickets = await data_extractor.get_all_tickets(request.project_key, request.project_id)
            
            if not tickets:
                logger.warning(f"No tickets found for project {request.project_id}")
                return {"status": "no_tickets", "message": "No tickets found", "tickets": []}
            
            logger.info(f"Found {len(tickets)} tickets for project {request.project_id}")
            
            # Convert tickets to DocumentEmbedding objects
            try:
                documents = [
                    DocumentEmbedding(
                        ticket_url=ticket.ticket_url,
                        issue_type=ticket.issue_type,
                        status=ticket.status,
                        priority=ticket.priority,
                        sprint=ticket.sprint,
                        key=ticket.ticket_api,
                        labels=ticket.labels,
                        resolution=ticket.resolution,
                        parent=ticket.parent,
                        assignee=ticket.assignee,
                        reporter=ticket.reporter,
                        resolutiondate=ticket.resolutiondate,
                        created_at=ticket.created_at,
                        updated_at=ticket.updated_at,
                        embedding_vector=ticket.embedding_vector
                    )
                    for ticket in tickets
                ]
            except Exception as e:
                logger.error(f"Error converting tickets to DocumentEmbedding objects: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Error processing ticket data"
                )
            
            # Generate and store embeddings
            try:
                await self.repository.add_embeddings(
                    domain=request.domain,
                    project_key=request.project_key,
                    internal_id=request.internal_id,
                    documents=documents
                )
            except Exception as e:
                logger.error(f"Error generating or storing embeddings: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Error generating or storing embeddings"
                )
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(documents)} documents",
                "tickets": tickets
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing documents: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing documents"
            )
