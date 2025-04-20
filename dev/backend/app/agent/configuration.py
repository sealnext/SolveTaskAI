"""
Configuration for the agent.
"""

from dataclasses import dataclass
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.misc.settings import settings


@dataclass
class AgentConfiguration:
	"""Configuration for the agent."""

	openai_model: str = settings.openai_model
	google_model: str = settings.google_model

	default_temperature: float = 0.0

	max_iterations: int = 10

	stream: bool = False

	def get_llm(
		self,
		custom_temperature: float | None = None,
		provider: Literal['openai', 'google'] | None = None,
	) -> BaseChatModel:
		"""Get the appropriate language model based on the configuration."""
		temperature = (
			custom_temperature if custom_temperature is not None else self.default_temperature
		)

		if provider == 'openai':
			return ChatOpenAI(
				api_key=settings.openai_api_key, model=self.openai_model, temperature=temperature
			)

		# Default to Google
		return ChatGoogleGenerativeAI(
			api_key=settings.google_api_key, model=self.google_model, temperature=temperature
		)
