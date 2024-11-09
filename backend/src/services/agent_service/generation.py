from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
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
        self.retrieve_tool = RetrieveDocuments(project=project, api_key=api_key)
        self.tool_node = ToolNode([self.retrieve_tool.to_tool()])

    async def generate_response(self, question: str, chat_history: List[dict]) -> tuple[str, Optional[str]]:
        """Generate a response using document retrieval with integrated query optimization."""
        logger.info("="*50)
        logger.info("Starting response generation")
        logger.info("="*50)
        
        formatted_history = self._format_chat_history(chat_history) if chat_history else ""
        logger.info(f"Original question: {question}")
        
        # Create the retrieval tool and bind it to the LLM
        llm_with_tools = self.llm.bind_tools(
            [self.retrieve_tool.to_tool()],
            tool_choice="auto"
        )
        
        # Single LLM call that handles both query optimization and tool usage decision
        prompt_content = main_prompt_template.format(
            question=question,
            chat_history=formatted_history
        )
        
        response = await llm_with_tools.ainvoke(
            [HumanMessage(content=prompt_content)]
        )
        
        if not response.tool_calls:
            logger.info("Direct response without document retrieval")
            return response.content, None
            
        # Extract the optimized query from the tool call
        tool_call = response.tool_calls[0]
        logger.debug(f"Tool call structure: {tool_call}")
        
        # Safely extract the query from the tool call arguments
        if isinstance(tool_call, dict):
            args = tool_call.get("args", {})
            if isinstance(args, str):
                import json
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"query": args}
            optimized_query = args.get("query", question)
        else:
            args = getattr(tool_call, "arguments", None)
            if args and isinstance(args, str):
                import json
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"query": args}
            optimized_query = args.get("query", question) if isinstance(args, dict) else question
            
        logger.info(f"Optimized query: {optimized_query}")
        
        # Create proper message sequence for tool node
        messages = [
            HumanMessage(content=prompt_content),
            response,  # This is the AIMessage containing tool calls
        ]
        
        # Execute retrieval with the optimized query
        tool_result = await self.tool_node.ainvoke({
            "messages": messages,
            "config": {"run_name": "document_retrieval"}
        })
        
        # Extract the retrieved documents from the tool result
        if isinstance(tool_result, dict) and "output" in tool_result:
            retrieved_docs = tool_result["output"]
        else:
            retrieved_docs = tool_result
            
        if not retrieved_docs:
            logger.info("No documents found - generating no-docs response")
            no_docs_response = await self.llm.ainvoke([
                HumanMessage(content=no_docs_prompt_template.format(
                    chat_history=formatted_history,
                    question=question
                ))
            ])
            return no_docs_response.content, None
            
        context = retrieved_docs
        logger.info("Generating final response with retrieved context")
        final_response = await self.llm.ainvoke([
            HumanMessage(content=final_answer_prompt_template.format(
                context=context,
                question=question
            ))
        ])
        
        logger.info("="*50)
        logger.info("Response generation completed")
        logger.info("="*50)
        
        return final_response.content, context

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