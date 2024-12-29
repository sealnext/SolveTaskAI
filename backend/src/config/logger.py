import logging
import colorlog
from .config import DEBUG_MODE
from functools import wraps
import inspect
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union
from dataclasses import asdict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage, FunctionMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
import json
from agent.state import AgentState

# Constants
MAX_LOGGER_NAME_LENGTH = 40
SEPARATOR_LENGTH = 80

# ANSI Colors for better visibility
class Colors:
    PINK = '\033[38;5;213m'  # pink
    ENDC = '\033[0m'     # reset

# Basic setup for root logger with enhanced formatting
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s: %(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S,%f"[:-3],
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
))

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    handlers=[handler]
)

# Set log levels for noisy loggers
for logger_name in [
    "sqlalchemy.engine", "sqlalchemy.pool",
    "openai", "openai._base_client",
    "httpcore.http11", "httpx", "httpcore.connection"
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

def _format_json(obj: Any, simplified: bool = True) -> str:
    """Format JSON objects for pretty printing with optional simplification."""
    if hasattr(obj, '__dict__'):
        obj = asdict(obj)
    
    if simplified and isinstance(obj, dict):
        # For context objects, show only function name
        if 'function' in obj and 'module' in obj:
            return f"{obj.get('function')}"
        
        # For tool calls, format args nicely
        if 'name' in obj and 'args' in obj:
            args = obj['args']
            if isinstance(args, dict):
                args_parts = []
                for k, v in args.items():
                    args_parts.append(f"{k}: {v!r}")
                return f"{obj['name']}({', '.join(args_parts)})"
            return f"{obj['name']}({args})"
        
        # For kwargs, format nicely
        parts = []
        for k, v in obj.items():
            parts.append(f"{k}: {v!r}")
        return ', '.join(parts)
    
    return json.dumps(obj, indent=2, default=str)

class GraphLogger:
    """Enhanced helper class for logging graph execution with proper context"""
    
    def __init__(self, step: Optional[int], node: str, triggers: list, logger_name: str = "agent.graph"):
        self.step = step
        self.node = node
        self.triggers = triggers
        self.logger = logging.getLogger(logger_name)
        self.start_time = time.time()
        self.metrics = {
            'token_usage': {},
            'execution_time': 0,
            'tool_calls': 0,
            'errors': 0
        }
        
    def log_header(self, title: str):
        """Log a section header"""
        prefix = f"Step {self.step} | " if self.step else ""
        header = "=" * 20 + f" {prefix}{title} " + "=" * 20
        padding = " " * (30 - len(self.logger.name))
        self.logger.info(f"{Colors.PINK}{header}{padding}{Colors.ENDC}")
        
    def log_flow(self):
        """Log flow information"""
        msg = f"[FLOW] Node: {self.node} | Triggers: {self.triggers}"
        self.logger.info(msg)
        
    def log_message(self, message: BaseMessage):
        """Log a message with proper formatting"""
        formatted = _format_message(message)
        if hasattr(message, 'response_metadata'):
            metadata = message.response_metadata
            if metadata and 'token_usage' in metadata:
                self.update_metrics(metadata)
        self.logger.info(formatted)
        
    def log_tool_call(self, name: str, args: Any):
        """Log a tool call with enhanced details"""
        self.metrics['tool_calls'] += 1
        tool_info = {
            'name': name,
            'args': args
        }
        self.logger.info(f"{Colors.WARNING}[TOOL-CALL]{Colors.ENDC} {_format_json(tool_info)}")
        
    def log_state(self, state: Dict):
        """Log current state information"""
        self.logger.debug(f"{Colors.BLUE}[STATE]{Colors.ENDC} Current State:\n{_format_json(state)}")
        
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log detailed error information"""
        self.metrics['errors'] += 1
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.error(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {_format_json(error_info)}")
        
    def update_metrics(self, metadata: Dict):
        """Update metrics from response metadata"""
        if 'token_usage' in metadata:
            usage = metadata['token_usage']
            current = self.metrics['token_usage']
            
            # Handle nested token usage metrics
            for key, value in usage.items():
                if isinstance(value, dict):
                    # If the value is a dictionary (nested metrics)
                    if key not in current:
                        current[key] = {}
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, (int, float)):
                            current[key][subkey] = current[key].get(subkey, 0) + subvalue
                elif isinstance(value, (int, float)):
                    # If the value is a number
                    current[key] = current.get(key, 0) + value

    def log_metrics(self):
        """Log accumulated metrics"""
        self.metrics['execution_time'] = time.time() - self.start_time
        tokens = self.metrics['token_usage']
        if tokens:
            self.logger.debug(f"[METRICS] time: {self.metrics['execution_time']:.2f}s, tokens: {tokens.get('total_tokens', 0)} = {tokens.get('prompt_tokens', 0)}p + {tokens.get('completion_tokens', 0)}c")

def _format_message(message: BaseMessage) -> str:
    """Format a message for logging."""
    if isinstance(message, HumanMessage):
        return f"[INPUT] (human): {message.content}"
    elif isinstance(message, AIMessage):
        # Handle tool calls if present
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for call in message.tool_calls:
                if isinstance(call, dict):
                    args = call.get('args', {})
                    if isinstance(args, str):
                        # If args is a string (JSON), parse it
                        try:
                            args = json.loads(args)
                        except:
                            pass
                    if isinstance(args, dict):
                        args_str = []
                        for k, v in args.items():
                            # Remove quotes from string values
                            if isinstance(v, str):
                                v = v.strip('"\'')
                            args_str.append(f"{k}={v}")
                        tool_calls.append(f"{call.get('name', 'unknown')}({', '.join(args_str)})")
                    else:
                        tool_calls.append(f"{call.get('name', 'unknown')}({args})")
                else:
                    args = call.args
                    if isinstance(args, dict):
                        args_str = []
                        for k, v in args.items():
                            if isinstance(v, str):
                                v = v.strip('"\'')
                            args_str.append(f"{k}={v}")
                        tool_calls.append(f"{call.name}({', '.join(args_str)})")
                    else:
                        tool_calls.append(f"{call.name}({args})")
            return f"[OUTPUT] LLM response with tool calls: {', '.join(tool_calls)}"
        return f"[OUTPUT] LLM response: {message.content}"
    elif isinstance(message, ToolMessage):
        return f"[INPUT] (tool): {message.content}"
    elif isinstance(message, FunctionMessage):
        return f"[TOOL] Response: {message.content}"
    else:
        return f"[MESSAGE] {message.content}"

def _format_tool_args(*args: Any, **kwargs: Any) -> str:
    """Enhanced tool arguments formatting with better structure"""
    formatted = {
        'positional_args': [],
        'keyword_args': {}
    }
    
    # Format positional arguments
    if args and len(args) > 0 and isinstance(args[0], dict):
        formatted['positional_args'] = [{k: v for k, v in args[0].items() if k != 'config'}]
    elif args:
        formatted['positional_args'] = [str(arg) for arg in args]
    
    # Format keyword arguments
    if kwargs:
        formatted['keyword_args'] = {k: v for k, v in kwargs.items() if k != 'config'}
    
    return _format_json(formatted)

def _is_tool(func: Any) -> bool:
    """Check if a function is a tool by looking at its attributes and base classes."""
    # Check if it's already a BaseTool instance
    if isinstance(func, BaseTool):
        return True
    
    # Check if it has tool-specific attributes
    if hasattr(func, 'args_schema') or hasattr(func, 'tool_schema'):
        return True
        
    # Check the function's name and module
    if func.__name__.endswith('_tool'):
        return True
        
    return False

def auto_log(logger_name: str = "agent.graph"):
    """
    Enhanced logging decorator that formats messages in a consistent way with headers and sections.
    Works with both async and sync functions, and handles both tools and nodes.
    Provides detailed metrics, timing information, and state tracking.
    """
    def decorator(func):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.propagate = False

        async def process_func(args, kwargs):
            start_time = time.time()
            config = kwargs.get('config', {})
            metadata = config.get('metadata', {})
            step = metadata.get('langgraph_step', '')
            node = metadata.get('langgraph_node', func.__name__)
            triggers = metadata.get('langgraph_triggers', [])

            # Create logger helper with enhanced capabilities
            graph_logger = GraphLogger(step, node, triggers, logger_name)

            # First log the header to mark the section
            header_text = func.__name__
            graph_logger.log_header(header_text)

            # Log context information
            user_id = metadata.get('user_id')
            thread_id = metadata.get('thread_id')
            if user_id and thread_id:
                logger.info(f"[CONTEXT] user_id: {user_id}, thread_id: {thread_id}")

            # Log input messages and state info for call_model
            if func.__name__ == 'call_model' and args and len(args) > 0:
                state = args[0]
                if isinstance(state, AgentState):
                    # Log project info if available
                    if state.project_data:
                        logger.info(f"[PROJECT] id: {state.project_data.get('id')}, name: {state.project_data.get('name')}")
                    
                    # Log state info
                    logger.info(f"[STATE] documents: {len(state.documents)}")
                    
                    # Log messages
                    if state.messages:
                        # For first step, show the initial human message
                        if step == 1:
                            first_msg = state.messages[0]
                            if isinstance(first_msg, HumanMessage):
                                logger.info(f"[INPUT] (human): {first_msg.content}")
                        # For other steps, show the last tool message
                        elif state.messages:
                            last_msg = state.messages[-1]
                            if isinstance(last_msg, (ToolMessage, HumanMessage)):
                                logger.info(f"[INPUT] ({last_msg.__class__.__name__.lower()}): {last_msg.content}")
            
            # Log flow information
            if step or triggers:
                graph_logger.log_flow()
            
            # Log kwargs if present (for tools)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'config'}
            if filtered_kwargs:
                logger.info(f"[KWARGS] {_format_json(filtered_kwargs)}")

            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Log execution time and result
                execution_time = time.time() - start_time
                
                if result is not None:
                    if isinstance(result, dict):
                        if "messages" in result:
                            for msg in result["messages"]:
                                # For call_model, also log model info
                                if hasattr(msg, 'response_metadata'):
                                    metadata = msg.response_metadata
                                    if metadata:
                                        model = metadata.get('model_name', '')
                                        finish_reason = metadata.get('finish_reason', '')
                                        if model or finish_reason:
                                            logger.info(f"[MODEL] name: {model}, finish_reason: {finish_reason}")
                                graph_logger.log_message(msg)
                        else:
                            graph_logger.log_message(result)
                    
                    # Log metrics if we have token usage, otherwise just execution time
                    tokens = graph_logger.metrics['token_usage']
                    if tokens and tokens.get('total_tokens', 0) > 0:
                        logger.info(f"[METRICS] time: {execution_time:.2f}s, tokens: {tokens['total_tokens']} = {tokens['prompt_tokens']}p + {tokens['completion_tokens']}c")
                    else:
                        logger.info(f"[EXECUTION TIME] {execution_time:.2f}s")
                
                return result
            except Exception as e:
                graph_logger.log_error(e)
                raise

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await process_func(args, kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import asyncio
                return asyncio.run(process_func(args, kwargs))
            return sync_wrapper
            
    return decorator
