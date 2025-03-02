"""
Configuration for the agent.
"""

from dataclasses import dataclass
from typing import Literal, Dict, Callable, Any, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel


@dataclass
class AgentConfiguration:
    """Configuration for the agent."""

    # Model provider to use
    provider: Literal["openai", "google"] = "google"

    # OpenAI model to use
    openai_model: str = "gpt-4o-mini"

    # Google Gemini model to use
    google_model: str = "gemini-2.0-flash"

    # Temperature for the model
    default_temperature: float = 0.0

    # Maximum number of iterations
    max_iterations: int = 10

    # Whether to stream responses
    stream: bool = False

    # Model provider factory mapping
    _MODEL_PROVIDERS: Dict[str, Callable[["AgentConfiguration", Optional[float]], BaseChatModel]] = {
        "openai": lambda config, temp=None: ChatOpenAI(
            model=config.openai_model, 
            temperature=temp if temp is not None else config.default_temperature
        ),
        "google": lambda config, temp=None: ChatGoogleGenerativeAI(
            model=config.google_model, 
            temperature=temp if temp is not None else config.default_temperature
        )
    }

    def get_llm(self, custom_temperature: Optional[float] = None) -> BaseChatModel:
        """Get the appropriate language model based on the configuration.
        
        Args:
            custom_temperature: Optional override for the temperature setting
            
        Returns:
            BaseChatModel: The configured language model
        """
        model_factory = self._MODEL_PROVIDERS.get(self.provider)
        if not model_factory:
            # Fallback to Google if provider is unknown
            model_factory = self._MODEL_PROVIDERS["google"]
        
        return model_factory(self, custom_temperature)
