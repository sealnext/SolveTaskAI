"""State management

This module defines the state structures used in the graph.
"""

from typing import Annotated, Any, Dict, Sequence

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage, BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel

from app.dto.api_key import ApiKey


def add_unique_documents(
	current_documents: Sequence[Document],
	new_documents: Sequence[Document],
) -> list[Document]:
	"""Custom reducer that adds documents without duplicates.

	Since Document objects are not hashable, we use a dictionary with document IDs
	or metadata keys to track uniqueness.
	"""
	# Create a dictionary to track unique documents by their metadata key or ID
	unique_docs = {}

	# Add current documents to the dictionary
	for doc in current_documents:
		# Use a unique identifier from metadata if available, otherwise use object id
		doc_id = doc.metadata.get('key', id(doc))
		unique_docs[doc_id] = doc

	# Add new documents, overwriting any with the same key
	for doc in new_documents:
		doc_id = doc.metadata.get('key', id(doc))
		unique_docs[doc_id] = doc

	# Return the values as a list
	return list(unique_docs.values())


class AgentState(BaseModel):
	question: str | None = None
	messages: Annotated[Sequence[AnyMessage], add_messages] = []
	documents: Annotated[Sequence[Document], add_unique_documents] = []
	project_data: Dict[str, Any] | None = None
	api_key: ApiKey | None = None

	model_config = {'arbitrary_types_allowed': True, 'frozen': True}

	def model_dump(self) -> dict:
		return {
			'messages': [
				{
					'content': msg.content,
					'type': msg.type,
					'additional_kwargs': msg.additional_kwargs,
				}
				if isinstance(msg, BaseMessage)
				else msg
				for msg in self.messages
			],
			'project_data': self.project_data,
		}
