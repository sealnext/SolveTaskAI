from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
	"""Schema for chat request"""

	question: str = Field(..., description='The question to be answered')
	project_id: int = Field(..., description='ID of the project')
	chat_id: str | None = Field(None, description='ID of the chat session')

	class Config:
		json_schema_extra = {
			'example': {
				'question': 'What are the main features implemented in the last sprint?',
				'project_id': 1,
				'chat_id': 'chat_123',
			}
		}


class QuestionResponse(BaseModel):
	"""Schema for chat response"""

	answer: str = Field(..., description='The answer to the question')
	chat_id: str = Field(..., description='ID of the chat session')

	class Config:
		json_schema_extra = {
			'example': {
				'answer': 'Based on the project documentation, in the last sprint the team implemented...',
				'chat_id': 'chat_123',
			}
		}
