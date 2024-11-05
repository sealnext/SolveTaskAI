from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import logging
from .rag.specialized_rag import RetrieveDocuments
from models import Project
from models.apikey import APIKey
from .prompts import (
    main_prompt_template,
    no_docs_prompt_template,
    final_answer_prompt_template
)
from config import OPENAI_MODEL
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm: Optional[ChatOpenAI] = None, project: Project = None, api_key: APIKey = None):
        self.llm = llm or ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        self.project = project
        self.api_key = api_key
        self.prompt = main_prompt_template

    async def generate_response(self, question: str, chat_history: List[dict]) -> tuple[str, Optional[str]]:
        """Generate a response using filtered chat history and retrieving documents if needed."""
        logger.info("="*50)
        logger.info("Starting response generation")
        logger.info("="*50)
        
        formatted_history = self._format_chat_history(chat_history) if chat_history else ""
        
        retrieve_tool = RetrieveDocuments(
            project=self.project,
            api_key=self.api_key
        )
        
        chain = self.prompt | self.llm.bind_tools(
            [retrieve_tool.to_tool()],
            tool_choice="auto"
        )
        
        logger.info(f"Original question: {question}")
        if formatted_history:
            logger.info("Chat history context available")
            logger.debug(f"Chat history: {formatted_history}")
        
        response = await chain.ainvoke({
            "question": question,
            "chat_history": formatted_history
        })
        
        logger.debug(f"Initial LLM response: {response}")
        logger.debug(f"Response has tool calls: {bool(response.tool_calls)}")
        
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            logger.info("-"*50)
            logger.info("Document retrieval requested")
            logger.info("-"*50)
            
            if tool_call["name"] == "RetrieveDocuments":
                args = tool_call["args"]
                search_query = args["search_query"]
                original_question = args["original_question"]
                
                logger.info("Query transformation:")
                logger.info(f"  Original: '{original_question}'")
                logger.info(f"  Optimized: '{search_query}'")
                
                documents = await retrieve_tool.invoke(search_query, original_question)
                logger.info(f"Retrieved {len(documents)} relevant documents")
                
                if not documents:
                    logger.info("No documents found - generating no-docs response")
                    no_docs_response = await self.llm.ainvoke([
                        HumanMessage(content=no_docs_prompt_template.format(
                            chat_history=formatted_history,
                            question=original_question
                        ))
                    ])
                    return no_docs_response.content, None
                
                context = self._format_docs(documents)
                logger.info("Generating final response with retrieved context")
                final_response = await self.llm.ainvoke([
                    HumanMessage(content=final_answer_prompt_template.format(
                        context=context,
                        question=original_question
                    ))
                ])
                logger.info("="*50)
                logger.info("Response generation completed")
                logger.info("="*50)
                return final_response.content, context
        
        logger.info("Direct response without document retrieval")
        return response.content, None

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

    def _format_chat_history(self, messages: List[dict]) -> str:
        """Format chat history for the prompt."""
        if not messages:
            return ""
            
        formatted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted.append(f"Context: {msg.content}")
            elif isinstance(msg, HumanMessage):
                formatted.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Assistant: {msg.content}")
        
        return "\n".join(formatted)