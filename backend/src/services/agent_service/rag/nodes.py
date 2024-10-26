from config import OPENAI_EMBEDDING_MODEL, DATABASE_URL
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from .state import AgentState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import re
import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging
from services.data_extractor import create_data_extractor
from config import NUMBER_OF_DOCS_TO_RETRIEVE

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
    logger.info("--- Retrieving documents node ---")
    question = state["question"]
    
    logger.info(f"Question: {question}")
    query_embedding = await embeddings_model.aembed_query(question)
    
    unique_identifier_project = f"{re.sub(r'^https?://|/$', '', state['project'].domain)}/{state['project'].key}/{state['project'].internal_id}"
    vector_store = create_vector_store(unique_identifier_project)
    
    documents_with_scores = await vector_store.asimilarity_search_with_score_by_vector(
        query_embedding,
        k=NUMBER_OF_DOCS_TO_RETRIEVE,
    )
    
    documents = await fetch_documents(state, documents_with_scores)

    logger.info(f"Retrieved {len(documents)} documents")
    for doc in documents:
        logger.info(f"Document key: {doc.metadata['key']}, Similarity score: {doc.metadata['similarity_score']}")
    
    return {"documents": documents}

doc_grader_instructions = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant."""

# Grader prompt
doc_grader_prompt = """Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}. 
This carefully and objectively assess whether the document contains at least some information that is relevant to the question.
Return JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question."""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_json_mode = llm.bind(response_format={"type": "json_object"})

async def grade_documents(state: AgentState) -> dict:
    logger.info("--- Grading documents node ---")
    
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    for doc in documents:
        logger.debug(f"Grading document: {doc}")
        doc_grader_prompt_formatted = doc_grader_prompt.format(
            document=doc.page_content, question=question
        )
        result = await llm_json_mode.ainvoke(
            [SystemMessage(content=doc_grader_instructions)]
            + [HumanMessage(content=doc_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]
        if grade.lower() == "yes":
            logger.debug("Document graded as relevant")
            filtered_docs.append(doc)
        else:
            logger.debug("Document graded as not relevant")

    return {"documents": filtered_docs}

# Prompt
rag_prompt = """You are an assistant for question-answering tasks. 
Here is the context to use to answer the question:

{context} 

Think carefully about the above context. 
Now, review the user question:

{question}

Provide an answer to this questions using only the above context. 
Use three sentences maximum and keep the answer concise.
Answer:"""

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate(state):
    logger.info("--- Generate node ---")
    
    question = state["question"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)

    # RAG generation
    docs_txt = format_docs(documents)
    rag_prompt_formatted = rag_prompt.format(context=docs_txt, question=question)
    generation = llm.invoke([HumanMessage(content=rag_prompt_formatted)])
    return {"generation": generation, "loop_step": loop_step + 1}

async def fetch_documents(state, documents_with_scores):
    data_extractor = create_data_extractor(state["api_key"])
    
    ticket_urls = [doc.metadata["key"] for doc, _ in documents_with_scores]
    fetched_documents = await data_extractor.get_tickets_parallel(ticket_urls)
    
    documents = []
    for (doc, score), fetched_doc in zip(documents_with_scores, fetched_documents):
        doc.page_content = fetched_doc.content
        doc.metadata["similarity_score"] = score
        documents.append(doc)
    
    return documents