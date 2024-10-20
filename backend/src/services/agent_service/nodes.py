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

async def access_documents_with_api_key(state: AgentState) -> AgentState:
    project_id = state["project"].id
    project_key = state["project"].key
    api_key = state["api_key"]
    
    if not all([project_id, project_key, api_key]):
        raise HTTPException(status_code=400, detail="Missing required state data")
    
    logger.info(f"Accessing documents for project {project_id}")
    data_extractor = create_data_extractor(api_key)
    tickets = await data_extractor.get_all_tickets(project_key, project_id)
    
    state["tickets"] = tickets
    return state

async def generate_embeddings(state: dict) -> dict:
    tickets = state["tickets"]
    project = state["project"]
    
    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', project.domain)}/{project.key}/{project.internal_id}"
    
    async with AsyncSessionLocal() as session:
        # Verificăm mai întâi dacă colecția există
        query = text("SELECT EXISTS (SELECT 1 FROM langchain_pg_collection WHERE name = :name)")
        result = await session.execute(query, {"name": unique_identifier_project})
        collection_exists = result.scalar()

        if collection_exists:
            logger.info(f"Collection {unique_identifier_project} already exists. Skipping embedding generation.")
            domain_with_slash = project.domain if project.domain.endswith('/') else f"{project.domain}/"
            return {"tickets": f"Collection for {domain_with_slash}browse/{project.key} already exists."}
        
        logger.info(f"Creating new collection for {unique_identifier_project} and adding all tickets.")
        
        # Creăm vector store doar dacă colecția nu există
        vector_store = create_vector_store(unique_identifier_project)
        
        docs = [
            Document(
                page_content="",
                metadata={
                    'ticket_url': ticket.ticket_url,
                    'issue_type': ticket.issue_type,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'sprint': ticket.sprint,
                    'key': ticket.ticket_api,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                },
                embedding=await embeddings_model.aembed_query(ticket.embedding_vector)
            )
            for ticket in tickets
        ]

        await vector_store.aadd_documents(docs)
    
    return {"tickets": tickets}

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
