"""
Configuration for the agent.
"""

from dataclasses import dataclass

@dataclass
class AgentConfiguration:
    """Configuration for the agent."""
    
    # OpenAI model to use
    model: str = "gpt-4o-mini"
    
    # Temperature for the model
    temperature: float = 0.0
    
    # Maximum number of iterations
    max_iterations: int = 10
    
    # Whether to stream responses
    stream: bool = False