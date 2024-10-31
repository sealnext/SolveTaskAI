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

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm: Optional[ChatOpenAI] = None, project: Project = None, api_key: APIKey = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.project = project
        self.api_key = api_key
        
        # Define the main prompt with RetrieveDocuments as a tool
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a specialized ticketing assistant helping users analyze and understand tickets, issues, and project documents from Jira, Confluence, and Azure DevOps."
                "\n\nYour Role:"
                "\n- Answer user questions about tickets, development issues, and project documentation."
                "\n- ALWAYS use RetrieveDocuments when there is no context or chat history available."
                "\n- Use RetrieveDocuments when the existing context is insufficient."
                "\n- Use chat history for context when available and sufficient."
                "\n\nGuidelines for Using Ticket Information:"
                "\n- **Always** include metadata (updated_at, created_at, status, sprint, issue_type, priority) for context, but **only** when needed and if it aids in answering the question. If the question is simple, answer in a simple manner."
                "\n- Link to ticket URLs when referencing information."
                "\n\nResponse Formatting:"
                "\n- For simple questions (e.g., 'Who solved this bug?'), give a brief, direct answer with only the essential information, such as the name and ticket link."
                "\n- For complex questions, provide an overview first, followed by detailed references and metadata."
                "\n\nIMPORTANT RULES:"
                "\n1. If there is NO chat history or context, you MUST use RetrieveDocuments first."
                "\n2. If chat history exists but doesn't contain relevant information, use RetrieveDocuments."
                "\n3. Only answer without RetrieveDocuments if you have sufficient context in chat history."
                "\n4. Keep answers concise where possible; expand only for complex inquiries."
            ),
            ("human", """Previous Context:
            {chat_history}

            Current Question:
            {question}

            Instructions:
            - If there is no previous context above, you MUST use RetrieveDocuments first
            - If the previous context exists but doesn't help answer the current question, use RetrieveDocuments
            - If the current question asks you to retrieve or search for information unrelated to the previous context, use RetrieveDocuments
            - Only use existing context if it's directly relevant to the current question""")
            ])

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

    async def generate_response(self, question: str, chat_history: str = "") -> tuple[str, Optional[str]]:
        """Generate a response using chat history and retrieving documents if needed.
        Returns tuple of (answer, context) where context might be None if no new documents were retrieved."""
        logger.info("Generating response")
        logger.debug(f"Chat history exists: {bool(chat_history)}")
        
        # Create tool with project and api_key
        retrieve_tool = RetrieveDocuments(
            project=self.project,
            api_key=self.api_key
        )
        
        # Force tool usage if no chat history
        tool_choice = {
            "type": "function",
            "function": {"name": "RetrieveDocuments"}
        } if not chat_history else "auto"
        
        chain = self.prompt | self.llm.bind_tools(
            [retrieve_tool.to_tool()],
            tool_choice=tool_choice
        )
        
        response = await chain.ainvoke({
            "question": question,
            "chat_history": chat_history
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
                    return (
                        "I couldn't find relevant information in this project's tickets or docs. "
                        "Please try asking about the project's tickets, issues, or development workflow instead.",
                        None
                    )
                
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