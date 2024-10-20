from config import OPENAI_EMBEDDING_MODEL, DATABASE_URL
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
from services.data_extractor.data_extractor_factory import create_data_extractor
from fastapi import HTTPException
from .state import AgentState
import re

import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

embeddings_model = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

def create_vector_store(unique_identifier_project: str):
    return PGVector(
        embeddings=embeddings_model,
        collection_name=unique_identifier_project,
        connection=DATABASE_URL,
        pre_delete_collection=False,
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

async def generate_embeddings(state):
    tickets = state["tickets"]
    project = state["project"]
    
    # ex: "sealnext.atlassian.net/PZ/10001"
    unique_identifier_project = re.sub(r'^https?://|/$', '', project.domain) + "/" + project.key + "/" + project.internal_id
    
    vector_store = create_vector_store(unique_identifier_project)
    
    docs = []
    for ticket in tickets:
        embedding = embeddings_model.embed_query(ticket.embedding_vector)
        
        doc = Document(
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
            embedding=embedding
        )
        docs.append(doc)
    
    vector_store.add_documents(docs)
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
