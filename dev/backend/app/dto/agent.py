from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentStreamInput(BaseModel):
	model_config = ConfigDict(extra='allow')

	# Either thread_id or project_id must be provided.
	project_id: int | None = Field(
		default=None, description='The project ID you want to talk to.', gt=0
	)
	thread_id: str | None = Field(
		default=None,
		description='The thread ID you want to talk to. If None, a new thread will be created.',
	)

	# Either message or action must be provided.
	message: str | None = Field(
		default=None,
		description='The message you want to send to the agent.',
	)
	action: str | None = Field(
		default=None,
		description='An action to perform, only if the last message was a command.',
		examples=['confirm'],
	)

	# Additional data when performing 'confirm' action.
	payload: dict | None = Field(
		default=None, description='Additional data, used with the "confirm" action.'
	)
	ticket: dict | None = Field(
		default=None, description='Ticket data, used with the "confirm" action.'
	)

	@model_validator(mode='after')
	def check_message_or_action_present(self) -> 'AgentStreamInput':
		"""
		Either message or action must be provided.
		"""
		if self.message is None and self.action is None:
			raise ValueError('You should either provide a message or an action.')
		return self

	@model_validator(mode='after')
	def check_thread_or_project_present(self) -> 'AgentStreamInput':
		"""
		Either thread_id or project_id must be provided.
		"""
		if self.thread_id is None and self.project_id is None:
			raise ValueError('You should provide either a thread_id or a project_id.')

		if self.thread_id is not None and self.project_id is not None:
			raise ValueError('You should provide either a thread_id or a project_id, not both.')
		return self

	@model_validator(mode='after')
	def check_confirm_data(self) -> 'AgentStreamInput':
		"""
		When performing 'confirm' action, payload and ticket must be provided.
		"""
		if self.action == 'confirm' and (self.payload is None and self.ticket is None):
			raise ValueError(
				'When performing "confirm" action, payload or ticket must be provided.'
			)
		return self
