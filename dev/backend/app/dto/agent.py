from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentStreamInput(BaseModel):
	model_config = ConfigDict(extra='allow')

	project_id: int = Field(..., description='The project ID you want to talk to.', gt=0)
	thread_id: Optional[str] = Field(
		default=None,
		description='The thread ID you want to talk to. If None, a new thread will be created.',
	)
	message: Optional[str] = Field(
		default=None,
	)
	action: Optional[str] = Field(
		default=None,
		description='An action to perform, only if the last message was a command.',
		examples=['confirm'],
	)
	payload: Optional[dict] = Field(
		default=None, description='Additional data to send with the message or action.'
	)
	ticket: Optional[dict] = Field(
		default=None, description="Ticket data, typically used with the 'confirm' action."
	)

	@model_validator(mode='after')
	def check_message_or_action_present(self) -> 'AgentStreamInput':
		"""
		Either message or action must be provided.
		"""
		if self.message is None and self.action is None:
			raise ValueError('You should either provide a message or an action.')
		return self
