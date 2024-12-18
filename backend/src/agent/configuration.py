"""
Configuration for the agent.
"""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AgentConfiguration:
    """Configuration for the agent."""
    
    # OpenAI model to use
    model: str = "gpt-4o-mini"
    
    # Temperature for the model
    temperature: float = 0.0
    
    # System prompt for the agent
    system_prompt: str = """You are a helpful AI assistant."""
    
    # Maximum number of iterations
    max_iterations: int = 10
    
    # Whether to stream responses
    stream: bool = False