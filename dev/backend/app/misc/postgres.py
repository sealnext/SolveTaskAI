from asyncio import shield
from logging import getLogger
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.misc.settings import settings
from app.model.base import Base

logger = getLogger(__name__)

async_db_engine = create_async_engine(
	url=str(settings.postgres_url), echo=True, pool_size=10, max_overflow=10, pool_pre_ping=True
)

async_db_session_factory = async_sessionmaker(
	bind=async_db_engine, autoflush=True, expire_on_commit=False
)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
	async with async_db_session_factory() as session:
		try:
			yield session
			await shield(session.commit())
		except:
			await shield(session.rollback())
			raise


async def init_db():
	logger.info('Initializing database...')

	async with async_db_engine.begin() as conn:
		# await conn.run_sync(Base.metadata.drop_all)
		await conn.run_sync(Base.metadata.create_all)

		# Create langchain_pg_collection table if not exists
		await conn.execute(
			text("""
            CREATE TABLE IF NOT EXISTS public.langchain_pg_collection (
                "uuid" uuid NOT NULL,
                "name" varchar NOT NULL,
                cmetadata json NULL,
                CONSTRAINT langchain_pg_collection_name_key UNIQUE (name),
                CONSTRAINT langchain_pg_collection_pkey PRIMARY KEY (uuid)
            )
        """)
		)

		# Create langchain_pg_embedding table if not exists
		await conn.execute(
			text("""
            CREATE TABLE IF NOT EXISTS public.langchain_pg_embedding (
                id varchar NOT NULL,
                collection_id uuid NULL,
                embedding public.vector NULL,
                "document" varchar NULL,
                cmetadata jsonb NULL,
                CONSTRAINT langchain_pg_embedding_pkey PRIMARY KEY (id)
            )
        """)
		)

		# Create indexes if not exist
		await conn.execute(
			text("""
            CREATE INDEX IF NOT EXISTS ix_cmetadata_gin
            ON public.langchain_pg_embedding USING gin (cmetadata jsonb_path_ops)
        """)
		)

		await conn.execute(
			text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_langchain_pg_embedding_id
            ON public.langchain_pg_embedding USING btree (id)
        """)
		)

		# Add foreign key if not exists
		await conn.execute(
			text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'langchain_pg_embedding_collection_id_fkey'
                ) THEN
                    ALTER TABLE public.langchain_pg_embedding
                    ADD CONSTRAINT langchain_pg_embedding_collection_id_fkey
                    FOREIGN KEY (collection_id)
                    REFERENCES public.langchain_pg_collection("uuid")
                    ON DELETE CASCADE;
                END IF;
            END $$;
        """)
		)
