from typing import Sequence

from app.dto.thread import Thread
from app.repository.thread import ThreadRepository


class ThreadService:
	def __init__(self, thread_repo: ThreadRepository):
		self.thread_repo = thread_repo

	async def get_project_id(self, thread_id: str) -> int:
		"""Get project ID from thread ID."""
		if not thread_id:
			raise ValueError('Thread ID is required')

		thread = await self.thread_repo.get(thread_id)
		if not thread:
			raise ValueError('Thread not found')

		if not thread['project_id']:
			raise ValueError('Project ID not found')
		return thread['project_id']

	async def get_user_threads(self, user_id: int) -> Sequence[Thread]:
		"""Get all threads for a user."""
		if not user_id:
			raise ValueError('User ID required')

		threads: Sequence[dict] = await self.thread_repo.get_all(user_id)
		if not threads:
			raise ValueError('No threads found')

		return [Thread.model_validate(thread) for thread in threads]

	async def delete_thread(self, user_id: int, thread_id: str) -> None:
		"""Delete thread and verify ownership."""
		if not thread_id:
			raise ValueError('Thread ID is required')

		exists = await self.thread_repo.verify_ownership(thread_id, user_id)
		if not exists:
			raise ValueError('Thread not found')

		await self.thread_repo.remove(thread_id)
