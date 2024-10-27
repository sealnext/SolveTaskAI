import json
import logging

from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .prompts import after_generation_instructions, after_generation_prompt
from config import OPENAI_MODEL

from .nodes import format_docs

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
llm_json_mode = llm.bind(response_format={"type": "json_object"})

async def grade_generation_hallucination_and_usefulness(state: dict) -> str:
    logger.info("--- Grade generation hallucination and usefulness ---")
    
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    max_retries = state.get("max_retries", 3)
    retry_retrieve_count = state.get("retry_retrieve_count", 0)
    ignore_tickets = state.get("ignore_tickets", [])

    after_generation_prompt_formatted = after_generation_prompt.format(
        documents=format_docs(documents),
        question=question,
        generation=generation.content
    )

    result = await llm_json_mode.ainvoke(
        [
            SystemMessage(content=after_generation_instructions),
            HumanMessage(content=after_generation_prompt_formatted)
        ]
    )

    grade_result = json.loads(result.content)
    binary_score = grade_result["binary_score"]
    explanation = grade_result["explanation"]

    logger.info(f"Grade result: {binary_score}")
    logger.info(f"Explanation: {explanation}")

    if binary_score == "yes":
        logger.info("Generation meets all criteria")
        return "useful"
    elif retry_retrieve_count < max_retries:
        logger.info("Generation does not meet all criteria, retrying retrieval")
        ignore_tickets.extend([doc.metadata["key"] for doc in documents])
        state["ignore_tickets"] = list(set(ignore_tickets))  # Remove duplicates
        state["retry_retrieve_count"] = retry_retrieve_count + 1
        return "not useful"
    else:
        logger.info("Max retries reached")
        return "max retries"

def decide_after_grading(state):
    """
    Determines whether to retry document retrieval or end the process

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    logger.info("---ASSESS GRADED DOCUMENTS---")
    documents = state["documents"]
    retry_retrieve_count = state.get("retry_retrieve_count", 0)

    if not documents and retry_retrieve_count < 3:  # Allow up to 2 retries (3 total attempts)
        logger.info("---DECISION: NO RELEVANT DOCUMENTS FOUND, RETRY RETRIEVAL---")
        return "retry"
    elif not documents:
        logger.info("---DECISION: MAX RETRIES REACHED---")
        return "max retries"
    else:
        logger.info("---DECISION: RELEVANT DOCUMENTS FOUND, END PROCESS---")
        return "generate"
