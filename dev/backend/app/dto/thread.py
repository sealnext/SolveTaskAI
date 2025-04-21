from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Thread(BaseModel):
	thread_id: str
	updated_at: datetime
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)
