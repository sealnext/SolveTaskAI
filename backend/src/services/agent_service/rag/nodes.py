from config import OPENAI_EMBEDDING_MODEL, DATABASE_URL
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
from services.data_extractor.data_extractor_factory import create_data_extractor
from fastapi import HTTPException
from .state import AgentState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import re
from sqlalchemy import text
import asyncio
from itertools import chain, islice

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

# Create a SQLAlchemy engine
engine = create_async_engine(DATABASE_URL)

# Create a session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def create_vector_store(unique_identifier_project: str):
    return PGVector(
        embeddings=embeddings_model,
        collection_name=unique_identifier_project,
        connection=DATABASE_URL,
        pre_delete_collection=False,
        async_mode=True
    )

# Self Rag Nodes
async def retrieve_documents(state):
    question = state["question"]
    query_embedding = await embeddings_model.embed_query(question)
    documents = await vector_store.asimilarity_search_by_vector(
        query_embedding,
        k=4,
        filter={"project_id": state.get("project_id")}
    )
    return {"documents": documents}

def generate_answer(state):
    print("--- Generating answer ---")
    
    question = state["question"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)
    
    docs_txt = format_documents(documents)
    rag_prompt = rag_prompt.format(context=docs_txt, question=question)
    generation = llm.invoke([HumanMessage(content=rag_prompt)])
    return {"generation": generation, "loop_step": loop_step + 1}

def grade_documents(state):
    print("--- Grading documents ---")
    
    question = state["question"]
    documents = state["documents"]
    
    filtered_documents = []
    for document in documents:
        doc_grader_prompt_formatted = doc_grader_prompt.format(document=document, question=question)
        result = llm_json_model.invoke([SystemMessage(content=doc_grader_instructions)] + [HumanMessage(content=doc_grader_prompt_formatted)])
        grade = json.loads(result.content)["binary_score"]
        
        if grade.lower() == "yes":
            print("--- Document included ---")
            filtered_documents.append(document)
        else:
            print("--- Document excluded ---")
    
    return {"documents": filtered_documents}
