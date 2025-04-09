from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
	name: str
	email: EmailStr


class UserCreateGitHub(BaseModel):
	github_id: str


class UserCreateGoogle(BaseModel):
	google_id: str


class UserCreateEmail(UserBase):
	password: str
