"""Repository for managing thread-user associations."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, insert, delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.model.associations import thread_user_association
import logging

logger = logging.getLogger(__name__)


class ThreadRepository:
    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def create(self, thread_id: str, user_id: str) -> None:
        """Create a new thread-user association."""
        logger.info(
            f"Creating thread-user association for thread {thread_id} and user {user_id}"
        )
        try:
            await self.session.execute(
                insert(thread_user_association).values(
                    thread_id=thread_id,
                    user_id=int(user_id),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to create thread-user association: {e}")
            raise

    async def get(self, thread_id: str) -> Optional[dict]:
        """Get thread by thread ID."""
        if not thread_id:
            return None

        try:
            result = await self.session.execute(
                select(
                    thread_user_association.c.thread_id,
                    thread_user_association.c.user_id,
                    thread_user_association.c.updated_at,
                ).where(thread_user_association.c.thread_id == thread_id)
            )
            row = result.first()
            return (
                {
                    "thread_id": row.thread_id,
                    "user_id": row.user_id,
                    "updated_at": row.updated_at,
                }
                if row
                else None
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            raise

    async def get_by_user_id(self, user_id: str) -> List[dict]:
        """Get all threads for a user."""
        if not user_id:
            return []

        try:
            result = await self.session.execute(
                select(
                    thread_user_association.c.thread_id,
                    thread_user_association.c.updated_at,
                )
                .where(thread_user_association.c.user_id == int(user_id))
                .order_by(thread_user_association.c.updated_at.desc())
            )
            rows = result.all()
            return (
                [
                    {"thread_id": row.thread_id, "updated_at": row.updated_at}
                    for row in rows
                ]
                if rows
                else []
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to get threads for user {user_id}: {e}")
            raise

    async def update_timestamp(self, thread_id: str) -> None:
        """Update the updated_at timestamp for a thread."""
        try:
            await self.session.execute(
                update(thread_user_association)
                .where(thread_user_association.c.thread_id == thread_id)
                .values(updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update timestamp for thread {thread_id}: {e}")
            raise

    async def verify_ownership(self, thread_id: str, user_id: str) -> bool:
        """Verify if thread belongs to user."""
        if not thread_id or not user_id:
            return False

        try:
            result = await self.session.execute(
                select(thread_user_association).where(
                    thread_user_association.c.thread_id == thread_id,
                    thread_user_association.c.user_id == int(user_id),
                )
            )
            return result.first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to verify ownership for thread {thread_id}: {e}")
            raise

    async def _get_checkpoint_ids(self, thread_id: str) -> List[str]:
        """Safely get checkpoint IDs for a thread."""
        try:
            checkpoint_ids_query = text("""
                SELECT checkpoint_id
                FROM checkpoints
                WHERE thread_id = :thread_id
            """)
            result = await self.session.execute(
                checkpoint_ids_query, {"thread_id": thread_id}
            )
            return [row[0] for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get checkpoint IDs for thread {thread_id}: {e}")
            raise

    async def _delete_checkpoint_related(
        self, checkpoint_ids: List[str], thread_id: str
    ) -> None:
        """Delete all checkpoint-related data."""
        try:
            # Delete from checkpoint_writes
            await self.session.execute(
                text("""
                DELETE FROM checkpoint_writes
                WHERE thread_id = :thread_id
                AND checkpoint_id = ANY(:checkpoint_ids)
                """),
                {"thread_id": thread_id, "checkpoint_ids": checkpoint_ids},
            )

            # Delete from checkpoint_blobs
            await self.session.execute(
                text("""
                DELETE FROM checkpoint_blobs
                WHERE thread_id = :thread_id
                """),
                {"thread_id": thread_id},
            )

            # Delete from checkpoints
            await self.session.execute(
                text("""
                DELETE FROM checkpoints
                WHERE thread_id = :thread_id
                """),
                {"thread_id": thread_id},
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to delete checkpoint data for thread {thread_id}: {e}"
            )
            raise

    async def remove(self, thread_id: str) -> None:
        """
        Remove thread and all associated data.
        This will cascade delete:
        - thread_user association
        - checkpoints
        - checkpoint_writes
        - checkpoint_blobs
        """
        if not thread_id:
            raise ValueError("thread_id cannot be None or empty")

        try:
            # Start by getting checkpoint IDs
            checkpoint_ids = await self._get_checkpoint_ids(thread_id)

            if checkpoint_ids:
                logger.info(
                    f"Deleting {len(checkpoint_ids)} checkpoints for thread {thread_id}"
                )
                await self._delete_checkpoint_related(checkpoint_ids, thread_id)

            # Finally delete the thread-user association
            result = await self.session.execute(
                delete(thread_user_association).where(
                    thread_user_association.c.thread_id == thread_id
                )
            )

            if result.rowcount == 0:
                logger.warning(
                    f"No thread-user association found for thread {thread_id}"
                )

            await self.session.commit()
            logger.info(f"Successfully deleted thread {thread_id} and all related data")

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to remove thread {thread_id}: {e}")
            raise
