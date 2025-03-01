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
"""

after_generation_prompt = """CONTEXT: \n\n {documents} \n\n QUESTION: \n\n {question} \n\n RESPONSE: \n\n {generation}.
Return JSON with the keys "binary_score" ("yes" or "no").
"""

doc_grader_instructions = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant."""

# Grader prompt
doc_grader_prompt = """Please evaluate if this document is relevant for answering the user's question.

Document Content and Metadata:
{document}

User query to get this document above was:
{question}

Evaluate if this document and its metadata contain information that are relevant to the user query.
Return a JSON object with a binary_score field that is either "yes" or "no".

Example response:
{{"binary_score": "yes"}}
"""

question_alternatives_instructions = """You are an expert at generating alternative search queries.
Given an original question, generate 5 alternative phrasings that:
1. Maintain the core intent of the original question
2. Use different keywords and sentence structures
3. Include both broader and more specific variations

Return a JSON object with an array of exactly 5 alternative questions."""

question_alternatives_prompt = """Original question: {question}

Generate 5 alternative ways to ask this question that might help retrieve different but relevant documents.
Return JSON with a single key "alternatives" containing an array of 5 strings."""
