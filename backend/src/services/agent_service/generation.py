from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from .rag.prompts import after_generation_instructions, after_generation_prompt
from .rag.specialized_rag import RetrieveDocuments
from models import Project
from models.apikey import APIKey
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm: Optional[ChatOpenAI] = None, project: Project = None, api_key: APIKey = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.project = project
        self.api_key = api_key
        
        # Modificăm prompt-ul pentru a fi mai flexibil în decizia de a folosi tool-ul
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a specialized ticketing assistant helping users analyze and understand tickets, issues, and project documents."
                "\n\nYour Role:"
                "\n- Answer user questions about tickets and project documentation."
                "\n- Use existing context when sufficient."
                "\n- Don't use RetrieveDocuments unless necessary is really really necessary:"
                "\n  1. There is no context at all"
                "\n  2. The existing context doesn't contain the specific information needed"
                "\n  3. The question asks about different tickets or aspects not covered in current context"
                "\n\nImportant:"
                "\n- If the current context contains the information needed, use it instead of retrieving new documents"
                "\n- Don't use RetrieveDocuments just because a question mentions tickets - check if current context is sufficient first"
            ),
            ("human", """Previous conversation and context:
            {chat_history}
            
            Current question: {question}
            
            Before using RetrieveDocuments, analyze if the existing context contains the information needed.""")
        ])

    async def generate_response(self, question: str, chat_history: List[dict]) -> tuple[str, Optional[str]]:
        """Generate a response using filtered chat history and retrieving documents if needed."""
        logger.info("Generating response")
        
        # Format chat history for the prompt
        formatted_history = self._format_chat_history(chat_history) if chat_history else ""
        
        # Create tool with project and api_key
        retrieve_tool = RetrieveDocuments(
            project=self.project,
            api_key=self.api_key
        )
        
        # Let the LLM decide when to use the tool based on the system prompt
        chain = self.prompt | self.llm.bind_tools(
            [retrieve_tool.to_tool()],
            tool_choice="auto"
        )
        
        response = await chain.ainvoke({
            "question": question,
            "chat_history": formatted_history
        })
        
        logger.debug(f"Response has tool calls: {bool(response.tool_calls)}")
        
        # Process tool calls if any
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            logger.info(f"Processing tool call: {tool_call}")
            
            if tool_call["name"] == "RetrieveDocuments":
                # Get the question directly from args dictionary
                search_question = tool_call["args"].get("question", question)
                
                # Execute retrieve workflow
                documents = await retrieve_tool.invoke(search_question)
                logger.info(f"Retrieved {len(documents)} documents")
                
                # If no documents found, return a default response
                if not documents:
                    # Generăm un răspuns mai inteligent bazat pe contextul existent
                    no_docs_prompt = f"""
                    No direct information was found in the project's documentation for this question.

                    Previous conversation context:
                    {formatted_history}

                    Current question: {question}

                    Instructions:
                    1. If the question is related to the previous context or project discussions, provide an informed response. Always highlight any uncertainties and the basis for your conclusions.
                    2. If the question is unrelated to the project, politely explain that responses are limited to project-specific topics and guide the user towards relevant queries.
                    3. Encourage rephrasing or refining the question if it seems vague or off-topic.
                    4. Never answer questions that are not related to the project, even if the user insists.

                    System Guardrails:
                    - Use content filters to automatically check for off-topic or inappropriate content.
                    - Implement monitoring to ensure responses remain within the scope of project-related discussions.
                    - Configure the system to provide alerts for potential override attempts or off-topic inquiries.

                    Remember to:
                    - Clearly articulate the level of certainty in your response.
                    - Explain the reasoning behind the ability or inability to provide a specific answer.
                    - Suggest alternative phrasings or further questions that could lead to more precise information related to the project, because you couldn't find anything in the project's data.
                    """

                    uncertain_response = await self.llm.ainvoke([HumanMessage(content=no_docs_prompt)])
                    return uncertain_response.content, None
                
                # Format documents for context
                context = self._format_docs(documents)
                
                # Generate final response with retrieved context
                final_prompt = f"""Based on the following context:

                {context}

                Answer the question: {question}

                Remember to:
                1. Reference specific tickets when providing information
                2. Include relevant metadata
                3. Keep the answer concise if the question is simple
                """
                final_response = await self.llm.ainvoke([HumanMessage(content=final_prompt)])
                return final_response.content, context
        
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