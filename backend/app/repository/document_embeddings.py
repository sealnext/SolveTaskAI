import asyncio
import re
from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, AsyncIterator, Dict, List, Union

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from app.dto.document_embeddings import DocumentEmbedding
from app.misc.postgres import async_db_engine
from app.misc.settings import settings

logger = getLogger(__name__)


class DocumentEmbeddingsRepository:
	def __init__(self, db_session):
		self.db_session = db_session

		self.embeddings_model = OpenAIEmbeddings(
			model=settings.openai_embedding_model,
			chunk_size=50,
			request_timeout=30,
			max_retries=3,
			show_progress_bar=True,
			skip_empty=True,
		)

	@asynccontextmanager
	async def _get_vector_store(self, unique_identifier: str):
		"""Get vector store instance with proper configuration."""
		try:
			vector_store = PGVector(
				embeddings=self.embeddings_model,
				collection_name=unique_identifier,
				connection=async_db_engine,
				pre_delete_collection=True,
				async_mode=True,
				create_extension=False,
			)
			yield vector_store
		except Exception as e:
			logger.error(f'Error in vector store: {str(e)}')
			raise

	async def add_embeddings(
		self,
		domain: str,
		project_key: str,
		external_id: str,
		documents: Union[List[DocumentEmbedding], AsyncIterator[DocumentEmbedding]],
		# total_documents: int | None = None,
	) -> None:
		"""Add embeddings to the vector store."""
		unique_identifier = self._get_unique_identifier(domain, project_key, external_id)
		logger.info(f'Starting embedding process for {unique_identifier}')

		# Time document conversion
		start_time = asyncio.get_running_loop().time()
		if isinstance(documents, AsyncIterator):
			docs_list = []
			async for doc in documents:
				docs_list.append(doc)
			documents = docs_list
		conversion_time = asyncio.get_running_loop().time() - start_time
		logger.info(f'Document conversion took {conversion_time:.2f}s')

		doc_count = len(documents)

		# Validate document count
		if doc_count == 0:
			logger.warning(f'No documents found for {unique_identifier}')
			raise ValueError('No documents to process. The project might be empty or inaccessible.')

		# Initialize timing metrics
		process_start = asyncio.get_running_loop().time()
		last_progress_time = process_start
		processed_count = 0
		failed_count = 0

		# Track API and DB timings
		total_embedding_time = 0
		total_db_time = 0

		async with self._get_vector_store(unique_identifier) as vector_store:
			vector_store_setup_time = asyncio.get_running_loop().time() - process_start
			logger.info(f'Vector store setup took {vector_store_setup_time:.2f}s')

			# Split documents into optimal batch sizes
			batch_size = 20  # Optimal batch size for OpenAI API
			batches = [documents[i : i + batch_size] for i in range(0, len(documents), batch_size)]

			# Process batches in parallel
			async def process_batch_with_stats(batch):
				nonlocal \
					processed_count, \
					failed_count, \
					total_embedding_time, \
					total_db_time, \
					last_progress_time
				try:
					batch_metrics = await self._process_batch(vector_store, batch)
					total_embedding_time += batch_metrics['embedding_time']
					total_db_time += batch_metrics['db_time']
					processed_count += len(batch)
				except Exception as e:
					failed_count += len(batch)
					logger.error(f'Batch processing error: {str(e)}')
				finally:
					# Log detailed progress with rates
					current_time = asyncio.get_running_loop().time()
					elapsed_total = max(current_time - process_start, 0.001)  # Minimum 1ms
					elapsed_since_last = max(
						current_time - last_progress_time, 0.001
					)  # Minimum 1ms

					if elapsed_since_last >= 1.0:  # Log every second
						progress = (processed_count / doc_count) * 100 if doc_count > 0 else 0
						total_rate = processed_count / elapsed_total
						current_rate = len(batch) / elapsed_since_last

						logger.info(
							f'Progress: {progress:.1f}% '
							f'({processed_count}/{doc_count} documents) | '
							f'Failed: {failed_count} | '
							f'Current rate: {current_rate:.2f} docs/sec | '
							f'Average rate: {total_rate:.2f} docs/sec'
						)
						last_progress_time = current_time

			# Process up to 5 batches concurrently
			concurrent_batches = 5
			# batch_start = asyncio.get_running_loop().time()
			for i in range(0, len(batches), concurrent_batches):
				batch_group = batches[i : i + concurrent_batches]
				await asyncio.gather(*(process_batch_with_stats(batch) for batch in batch_group))

			# Log final detailed stats
			total_time = asyncio.get_running_loop().time() - process_start
			logger.info(
				f'\nProcessing Summary:\n'
				f'- Total documents: {doc_count}\n'
				f'- Successful: {processed_count} ({(processed_count / doc_count * 100):.1f}%)\n'
				f'- Failed: {failed_count}\n'
				f'- Total time: {total_time:.2f}s\n'
				f'- Average rate: {processed_count / total_time:.2f} docs/sec\n'
				f'\nBreakdown:\n'
				f'- Document conversion: {conversion_time:.2f}s ({conversion_time / total_time * 100:.1f}%)\n'
				f'- Vector store setup: {vector_store_setup_time:.2f}s ({vector_store_setup_time / total_time * 100:.1f}%)\n'
				f'- Embedding generation: {total_embedding_time:.2f}s ({total_embedding_time / total_time * 100:.1f}%)\n'
				f'- Database operations: {total_db_time:.2f}s ({total_db_time / total_time * 100:.1f}%)'
			)

	async def _process_batch(
		self, vector_store: PGVector, documents: List[DocumentEmbedding]
	) -> Dict[str, float]:
		"""
		Process a batch of documents by generating embeddings and storing them.
		Uses optimized batching and parallel processing for better performance.

		Args:
		    vector_store: The PGVector instance to store embeddings
		    documents: List of documents to process in this batch

		Returns:
		    Dict containing timing metrics for the batch processing
		"""
		if not documents:
			return {'embedding_time': 0, 'db_time': 0, 'prep_time': 0}

		try:
			# Time metadata preparation
			prep_start = asyncio.get_running_loop().time()
			embedding_texts = [doc.embedding_vector for doc in documents]
			metadatas = [self._prepare_metadata(doc) for doc in documents]
			prep_time = max(asyncio.get_running_loop().time() - prep_start, 0.001)  # Minimum 1ms

			# Time the embedding generation
			embed_start = asyncio.get_running_loop().time()
			embeddings = await self.embeddings_model.aembed_documents(embedding_texts)
			embed_time = max(asyncio.get_running_loop().time() - embed_start, 0.001)  # Minimum 1ms

			# Time the database operation
			db_start = asyncio.get_running_loop().time()
			await vector_store.aadd_embeddings(
				texts=[''] * len(embeddings),  # We store content in metadata
				embeddings=embeddings,
				metadatas=metadatas,
				batch_size=len(embeddings),  # Use single bulk operation
			)
			db_time = max(asyncio.get_running_loop().time() - db_start, 0.001)  # Minimum 1ms

			# Calculate rates safely
			prep_rate = len(documents) / prep_time if prep_time > 0 else 0
			embed_rate = len(documents) / embed_time if embed_time > 0 else 0
			db_rate = len(documents) / db_time if db_time > 0 else 0

			# Log detailed batch metrics
			logger.info(
				f'Batch processing metrics:\n'
				f'- Metadata preparation: {prep_time:.2f}s ({prep_rate:.2f} docs/s)\n'
				f'- Embedding generation: {embed_time:.2f}s ({embed_rate:.2f} docs/s)\n'
				f'- Database insertion: {db_time:.2f}s ({db_rate:.2f} docs/s)\n'
				f'- Total batch time: {prep_time + embed_time + db_time:.2f}s'
			)

			return {
				'embedding_time': embed_time,
				'db_time': db_time,
				'prep_time': prep_time,
			}

		except Exception as e:
			logger.error(f'Error processing batch: {str(e)}')
			raise

	async def collection_exists(self, unique_identifier: str) -> bool:
		"""Check if collection exists."""
		async with self._get_vector_store(unique_identifier) as vector_store:
			return await vector_store.acollection_exists()

	async def delete_collection(self, domain: str, project_key: str, external_id: str) -> None:
		"""Delete a collection."""
		unique_identifier = self._get_unique_identifier(domain, project_key, external_id)
		logger.debug(f'Attempting to delete collection: {unique_identifier}')

		async with self._get_vector_store(unique_identifier) as vector_store:
			await vector_store.adelete_collection()
			logger.info(f'Successfully deleted collection: {unique_identifier}')

	def _get_unique_identifier(self, domain: str, project_key: str, external_id: str) -> str:
		"""Generate a unique identifier for the collection."""
		return f'{re.sub(r"^https?://|/$", "", domain)}/{project_key}/{external_id}'

	def _prepare_metadata(self, doc: DocumentEmbedding) -> Dict[str, Any]:
		"""Prepare metadata for document, excluding null values and empty lists."""
		metadata = {
			'ticket_url': doc.ticket_url,
			'key': doc.key,
			'created_at': doc.created_at.isoformat(),
			'updated_at': doc.updated_at.isoformat(),
		}

		# Add optional fields only if they have values
		if doc.issue_type:
			metadata['issue_type'] = doc.issue_type
		if doc.status:
			metadata['status'] = doc.status
		if doc.priority:
			metadata['priority'] = doc.priority
		if doc.sprint:
			metadata['sprint'] = doc.sprint
		if doc.labels and len(doc.labels) > 0:
			metadata['labels'] = doc.labels
		if doc.resolution:
			metadata['resolution'] = doc.resolution
		if doc.parent:
			metadata['parent'] = doc.parent
		if doc.assignee:
			metadata['assignee'] = doc.assignee
		if doc.reporter:
			metadata['reporter'] = doc.reporter
		if doc.resolutiondate:
			metadata['resolutiondate'] = doc.resolutiondate.isoformat()

		return metadata
