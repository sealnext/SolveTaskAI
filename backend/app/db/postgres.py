from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config.config import DATABASE_URL
from logging import getLogger

from app.models.base import Base


logger = getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


async def init_db():
    logger.info("Initializing pgvector database...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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