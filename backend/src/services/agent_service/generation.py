from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging
from .rag.prompts import rag_prompt, after_generation_instructions, after_generation_prompt

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.llm_json_mode = self.llm.bind(response_format={"type": "json_object"})

    def _format_docs(self, documents: List[dict]) -> str:
        """Format documents for the prompt."""
        if not documents:
            return ""
            
        formatted_docs = [
            f"Ticket {i+1}: '{doc.metadata.get('ticket_url', 'No URL provided')}'\n\n"
            f"Content: {doc.page_content}\n\n"
            f"Metadata: {doc.metadata}"
            for i, doc in enumerate(documents)
        ]
        
        return f"Retrieved documents:\n\n" + "\n\n".join(formatted_docs)

    async def generate_response(self, question: str, documents: List[dict], chat_history: str = "") -> str:
        """Generate a response using the retrieved documents and chat history."""
        logger.info("Generating response")
        
        context = self._format_docs(documents) if documents else ""
        
        # Generate initial response
        rag_prompt_formatted = rag_prompt.format(
            context=context,
            chat_history=chat_history,
            question=question
        )
        generation = await self.llm.ainvoke([HumanMessage(content=rag_prompt_formatted)])
        
        # Grade the generation
        after_generation_prompt_formatted = after_generation_prompt.format(
            documents=context,
            question=question,
            generation=generation.content
        )
        
        result = await self.llm_json_mode.ainvoke([
            SystemMessage(content=after_generation_instructions),
            HumanMessage(content=after_generation_prompt_formatted)
        ])
        
        grade_result = json.loads(result.content)
        binary_score = grade_result["binary_score"].lower()
        
        logger.info(f"Generation grade: {binary_score}")
        
        if binary_score == "yes":
            return generation.content
        else:
            # If generation is not good enough, try to improve it
            improved_prompt = (
                f"I need to improve this response. Here's what we know:\n\n"
                f"Question: {question}\n"
                f"Context: {context}\n"
                f"Chat History: {chat_history}\n\n"
                f"Previous response: {generation.content}\n\n"
                f"Please provide a more accurate and detailed response based on the available information."
            )
            
            improved_generation = await self.llm.ainvoke([HumanMessage(content=improved_prompt)])
            return improved_generation.content 