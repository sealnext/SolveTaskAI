"""
Configuration for the agent.
"""

from dataclasses import dataclass
from typing import Any, List, Literal, Optional

from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import Field

from app.misc.settings import settings


async def update_token_usage(
	checkpointer: AsyncPostgresSaver, thread_id: str, input_tokens: int, output_tokens: int
) -> None:
	"""Update token usage for a thread."""
	if not checkpointer or not thread_id:
		return

	async with checkpointer._cursor() as cur:
		await cur.execute(
			"""
			UPDATE thread_user
			SET
				updated_at = NOW(),
				input_tokens = COALESCE(input_tokens, 0) + %s,
				output_tokens = COALESCE(output_tokens, 0) + %s
			WHERE thread_id = %s
			""",
			(input_tokens, output_tokens, thread_id),
		)


class CustomGoogleLLM(ChatGoogleGenerativeAI):
	"""Custom Google LLM with post-processing capabilities."""

	checkpointer: Optional[AsyncPostgresSaver] = Field(default=None, exclude=True)

	def __init__(self, checkpointer: AsyncPostgresSaver = None, **kwargs):
		super().__init__(checkpointer=checkpointer, **kwargs)

	async def ainvoke(
		self,
		input: LanguageModelInput,
		config: Optional[RunnableConfig] = None,
		*,
		stop: Optional[List[str]] = None,
		**kwargs: Any,
	) -> BaseMessage:
		"""Invoke the LLM and perform post-processing."""
		response = await super().ainvoke(input, config=config, stop=stop, **kwargs)

		thread_id = config.get('configurable', {}).get('thread_id') if config else None
		if thread_id and self.checkpointer and hasattr(response, 'usage_metadata'):
			input_tokens = response.usage_metadata.get('input_tokens', 0)
			output_tokens = response.usage_metadata.get('output_tokens', 0)

			await update_token_usage(self.checkpointer, thread_id, input_tokens, output_tokens)

		return response


class CustomOpenAILLM(ChatOpenAI):
	"""Custom OpenAI LLM with post-processing capabilities."""

	checkpointer: Optional[AsyncPostgresSaver] = Field(default=None, exclude=True)

	def __init__(self, checkpointer: AsyncPostgresSaver = None, **kwargs):
		super().__init__(checkpointer=checkpointer, **kwargs)

	async def ainvoke(
		self,
		input: LanguageModelInput,
		config: Optional[RunnableConfig] = None,
		*,
		stop: Optional[List[str]] = None,
		**kwargs: Any,
	) -> BaseMessage:
		"""Invoke the LLM and perform post-processing."""
		response = await super().ainvoke(input, config=config, stop=stop, **kwargs)

		thread_id = config.get('configurable', {}).get('thread_id') if config else None
		if thread_id and self.checkpointer and hasattr(response, 'usage_metadata'):
			input_tokens = response.usage_metadata.get('input_tokens', 0)
			output_tokens = response.usage_metadata.get('output_tokens', 0)

			await update_token_usage(self.checkpointer, thread_id, input_tokens, output_tokens)

		return response


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
		checkpointer: AsyncPostgresSaver | None = None,
	) -> BaseChatModel:
		"""Get the appropriate language model based on the configuration.

		Args:
			custom_temperature: Optional custom temperature setting
			provider: Optional provider specification ('openai' or 'google')
			checkpointer: Optional checkpointer for token tracking

		Returns:
			Configured language model
		"""
		temperature = (
			custom_temperature if custom_temperature is not None else self.default_temperature
		)

		if provider == 'openai':
			return CustomOpenAILLM(
				checkpointer=checkpointer,
				api_key=settings.openai_api_key,
				model=self.openai_model,
				temperature=temperature,
			)

		return CustomGoogleLLM(
			checkpointer=checkpointer,
			api_key=settings.google_api_key,
			model=self.google_model,
			temperature=temperature,
		)
