import json
import logging

from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .nodes import format_docs

logger = logging.getLogger(__name__)

# Hallucination grader instructions
hallucination_grader_instructions = """
You are a teacher grading a quiz. 
You will be given FACTS and a STUDENT ANSWER. 
Here is the grade criteria to follow:

(1) Ensure the STUDENT ANSWER is grounded in the FACTS. 

(2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Score:
A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 
A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.
Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 
Avoid simply stating the correct answer at the outset."""

hallucination_grader_prompt = """FACTS: \n\n {documents} \n\n STUDENT ANSWER: {generation}. 
Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER is grounded in the FACTS. And a key, explanation, that contains an explanation of the score."""

# Answer grader instructions
answer_grader_instructions = """You are a teacher grading a quiz. 
You will be given a QUESTION and a STUDENT ANSWER. 
Here is the grade criteria to follow:
(1) The STUDENT ANSWER helps to answer the QUESTION
Score:
A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 
The student can receive a score of yes if the answer contains extra information that is not explicitly asked for in the question.
A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.
Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 
Avoid simply stating the correct answer at the outset."""

answer_grader_prompt = """QUESTION: \n\n {question} \n\n STUDENT ANSWER: {generation}. 
Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER meets the criteria. And a key, explanation, that contains an explanation of the score."""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_json_mode = llm.bind(response_format={"type": "json_object"})

def grade_generation_hallucination_and_usefulness(state):
    logger.info("--- Grade generation hallucination and usefulness ---")
    
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    max_retries = state.get("max_retries", 3)

    hallucination_grader_prompt_formatted = hallucination_grader_prompt.format(
        documents=format_docs(documents), generation=generation.content
    )
    result = llm_json_mode.invoke(
        [SystemMessage(content=hallucination_grader_instructions)]
        + [HumanMessage(content=hallucination_grader_prompt_formatted)]
    )
    grade = json.loads(result.content)["binary_score"]

    # Check hallucination
    if grade == "yes":
        logger.debug("hallucination grade is yes")
        # Check question-answering
        answer_grader_prompt_formatted = answer_grader_prompt.format(
            question=question, generation=generation.content
        )
        result = llm_json_mode.invoke(
            [SystemMessage(content=answer_grader_instructions)]
            + [HumanMessage(content=answer_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]
        if grade == "yes":
            logger.debug("question-answering grade is yes")
            return "useful"
        elif state["loop_step"] <= max_retries:
            logger.debug("question-answering grade is no")
            return "not useful"
        else:
            logger.debug("max retries reached")
            return "max retries"
    elif state["loop_step"] <= max_retries:
        logger.debug("hallucination grade is no")
        return "not supported"
    else:
        logger.debug("max retries reached")
        return "max retries"
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    