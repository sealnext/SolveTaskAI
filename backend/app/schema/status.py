from pydantic import BaseModel


class StatusSchema(BaseModel):
    id: str
    name: str
