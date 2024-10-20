import json


def decide_to_generate(state):
    print("--- Deciding to generate ---")
    question = state["question"]
    documents = state["documents"]
    
    if len(documents) == 0:
        return "end"
    else:
        return "continue"

def grade_generation_hallucination_and_usefulness(state):
    print("--- Grading generation hallucination and usefulness ---")
    question = state["question"]
    generation = state["generation"]
    documents = state["documents"]
    max_retries = state.get("max_retries", 3)
    
    hallucination_and_usefulness_prompt_formatted = hallucination_and_usefulness_prompt.format(documents=format_documents(documents), question=question, generation=generation.content)
    result = llm_json_model.invoke([SystemMessage(content=hallucination_and_usefulness_instructions)] + [HumanMessage(content=hallucination_and_usefulness_prompt_formatted)])
    grade = json.loads(result.content)["binary_score"]
    
    if grade.lower() == "yes":
        return "useful"
    elif state["loop_step"] <= max_retries:
        return "not useful"
    else:
        return "max retries"
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    