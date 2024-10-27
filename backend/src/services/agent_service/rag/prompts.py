after_generation_instructions = """You are evaluating the quality of a response based on specific criteria. You will be given a CONTEXT, a QUESTION, and a RESPONSE. Your job is to assess the RESPONSE in relation to the CONTEXT and QUESTION, focusing on three core areas:

1. **Grounded in Facts (Hallucination Check):** Verify if the RESPONSE is based on the CONTEXT provided and does not contain information that deviates from it. The RESPONSE should stay within the scope of the CONTEXT.
  
2. **Relevance to the Question:** Confirm if the RESPONSE helps answer the QUESTION. Extra relevant information is acceptable as long as it does not stray from the QUESTION’s intent.
  
3. **Overall Quality (Answer Check):** Ensure that the RESPONSE sufficiently addresses the QUESTION based on the CONTEXT. Consider both accuracy and clarity in how well the RESPONSE aligns with what was asked.

**Score:**  
- A score of "yes" means the RESPONSE meets all criteria above.  
- A score of "no" means one or more criteria are not met.  
Provide a clear explanation that outlines your reasoning for the score. Walk through each criterion, detailing where the RESPONSE succeeds or falls short.

Output JSON with two keys:  
- `binary_score`: "yes" or "no" based on whether the RESPONSE meets all criteria.  
- `explanation`: an explanation describing the score rationale.
"""

after_generation_prompt = """CONTEXT: \n\n {documents} \n\n QUESTION: \n\n {question} \n\n RESPONSE: \n\n {generation}. 
Return JSON with the keys "binary_score" ("yes" or "no") and "explanation" (step-by-step reasoning for the score).
"""

doc_grader_instructions = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant."""

# Grader prompt
doc_grader_prompt = """Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}. 
This carefully and objectively assess whether the document contains at least some information that is relevant to the question.
Return JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question."""

# Generation prompt
rag_prompt = """You are an assistant for question-answering tasks. 
You will be given a list of tickets for context, each ticket has a ticket_url, page_content and metadata.

You can use the metadata to get more information about the ticket when responding.
You can use the ticket_url when responding, to link to the ticket in your answer as reference.
You can use the page_content to answer the question, this is the context you have to work with.
The page_context is divided into three sections, title, description and comments. You can use all of them to answer the question.

{context} 

Think carefully about the above context. 
Now, review the user question:

{question}

If you can answer the question, then use only the above context.
Use five sentences maximum and keep the answer concise.
Answer:"""