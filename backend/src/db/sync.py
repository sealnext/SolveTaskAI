import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from models import Base
from db.session import engine
from config import SYNC_DATABASE
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def create_langchain_tables():
    """Create the tables needed by LangChain's PGVector if they don't exist."""
    async with engine.begin() as conn:
        # Create vector extension if not exists (needed for the vector type)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create langchain_pg_collection table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.langchain_pg_collection (
                "uuid" uuid NOT NULL,
                "name" varchar NOT NULL,
                cmetadata json NULL,
                CONSTRAINT langchain_pg_collection_name_key UNIQUE (name),
                CONSTRAINT langchain_pg_collection_pkey PRIMARY KEY (uuid)
            )
        """))
        
        # Create langchain_pg_embedding table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.langchain_pg_embedding (
                id varchar NOT NULL,
                collection_id uuid NULL,
                embedding public.vector NULL,
                "document" varchar NULL,
                cmetadata jsonb NULL,
                CONSTRAINT langchain_pg_embedding_pkey PRIMARY KEY (id)
            )
        """))
        
        # Create indexes if not exist
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_cmetadata_gin 
            ON public.langchain_pg_embedding USING gin (cmetadata jsonb_path_ops)
        """))
        
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_langchain_pg_embedding_id 
            ON public.langchain_pg_embedding USING btree (id)
        """))
        
        # Add foreign key if not exists
        await conn.execute(text("""
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
        """))

async def sync_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_langchain_tables()

async def sync_database():
    if SYNC_DATABASE:
        logger.info("Syncing database...")
        await sync_db()
    else:
        logger.info("Database synchronization is disabled.")

if __name__ == "__main__":
    asyncio.run(sync_database())