import logging
import colorlog
from .config import DEBUG_MODE, SQL_LOGGING
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from functools import wraps
import inspect
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

# Calculate max length for logger name padding
MAX_LOGGER_NAME_LENGTH = 30

log_format = (
    "%(log_color)s%(levelname)s: %(asctime)s - %(name)-{0}s - %(message)s".format(MAX_LOGGER_NAME_LENGTH)
)

log_colors = {
    'DEBUG': 'yellow',
    'INFO': 'green',
    'WARNING': 'red',
    'ERROR': 'bold_red',
    'CRITICAL': 'bold_red',
}

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    log_format, log_colors=log_colors
))

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    handlers=[handler],
)

sqlalchemy_log_level = logging.WARNING
conversation_log_level = logging.INFO

logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_log_level)
logging.getLogger("sqlalchemy.pool").setLevel(sqlalchemy_log_level)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.getLogger("conversation").setLevel(conversation_log_level)

logging.getLogger("services.agent_service.ticketing_tool").setLevel(logging.INFO)
logging.getLogger("services.agent_service.nodes").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def log_message(message: str, prefix: str = "", logger_name: str = __name__):
    """Utility function for simple message logging"""
    log = logging.getLogger(logger_name)
    log.info(f"[{prefix}] {message}" if prefix else message)

def log_flow_details(title: str, details: dict, logger_name: str = __name__):
    """Log only flow-relevant details"""
    log = logging.getLogger(logger_name)
    if title == "Flow Info":
        log_message(f"Step: {details.get('step')} | Node: {details.get('node')} | Triggers: {details.get('triggers')}", "FLOW", logger_name)

class GraphLogger:
    """Helper class for logging graph execution with proper context"""
    
    def __init__(self, step: int, node: str, triggers: list, logger_name: str = "agent.graph"):
        self.step = step
        self.node = node
        self.triggers = triggers
        self.logger = logging.getLogger(logger_name)
        
    def response(self, message: str):
        """Log a response message"""
        log_message(message, "OUTPUT", self.logger.name)
        
    def _log_header(self, title: str, separator: str):
        """Helper method to log section headers"""
        prefix = f"Step {self.step} | " if self.step else ""
        header = separator * 20 + f" {prefix}{title} " + separator * 20
        # Calculate padding to align with logger name
        padding = " " * (MAX_LOGGER_NAME_LENGTH - len(self.logger.name))
        self.logger.info(header + padding)

def log_with_context(config: RunnableConfig, logger_name: str = "agent.graph"):
    """Create a logging context from config"""
    metadata = config.get('metadata', {})
    return GraphLogger(
        step=metadata.get('langgraph_step'),
        node=metadata.get('langgraph_node'),
        triggers=metadata.get('langgraph_triggers', []),
        logger_name=logger_name
    )

def auto_log(logger_name: str = "agent.graph"):
    """Smart decorator that automatically detects if it's a tool or node and applies appropriate logging"""
    def decorator(func: Callable):
        is_async = inspect.iscoroutinefunction(func)
        is_tool = any(isinstance(d, tool) for d in getattr(func, '__decorators__', []))
        
        if is_async:  # It's a node
            @wraps(func)
            async def async_wrapper(state: Any, config: RunnableConfig):
                # Setup logging
                logger = log_with_context(config, logger_name)
                logger._log_header(f"Node: {logger.node}", "=")
                
                # Log flow info
                metadata = config.get('metadata', {})
                flow_info = {
                    "step": metadata.get('langgraph_step'),
                    "node": metadata.get('langgraph_node'),
                    "triggers": metadata.get('langgraph_triggers', [])
                }
                log_flow_details("Flow Info", flow_info, logger_name)
                
                # Log input message if available
                if hasattr(state, 'messages') and state.messages:
                    last_message = state.messages[-1]
                    log_message(f"User message: {last_message.content}", "INPUT", logger_name)
                
                # Execute node
                result = await func(state, config)
                
                # Log response if available
                if isinstance(result, dict) and 'messages' in result and result['messages']:
                    response = result['messages'][-1]
                    logger.response(f"LLM response: {response.content if hasattr(response, 'content') else response}")
                    
                return result
                
            return async_wrapper
        else:  # It's a tool
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Extract config and query from args/kwargs
                config = kwargs.get('config', args[1] if len(args) > 1 else None)
                query = kwargs.get('query', args[0] if args else None)
                
                if not config:
                    return func(*args, **kwargs)
                    
                # Setup logging
                logger = log_with_context(config, logger_name)
                logger._log_header(f"Tool: {func.__name__}", ".")
                
                # Log flow info
                metadata = config.get('metadata', {})
                flow_info = {
                    "step": metadata.get('langgraph_step'),
                    "node": metadata.get('langgraph_node'),
                    "triggers": metadata.get('langgraph_triggers', [])
                }
                log_flow_details("Flow Info", flow_info, logger_name)
                
                # Log query if available
                if query:
                    log_message(f"Query: {query}", "TOOL-INPUT", logger_name)
                
                # Execute tool
                result = func(*args, **kwargs)
                return result
                
            return sync_wrapper
    return decorator
