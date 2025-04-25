from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr


def _validate_password(password: str) -> str:
	min_length: int = 12

	has_letter: bool = False
	has_digit: bool = False
	has_symbol: bool = False

	if len(password) < min_length:
		raise ValueError(f'Password must be at least {min_length} characters long.')

	for char in password:
		if char.isalpha():
			has_letter = True
		elif char.isdigit():
			has_digit = True
		else:
			has_symbol = True

	if not has_letter:
		raise ValueError('Password must contain at least one letter.')

	if not has_digit:
		raise ValueError('Password must contain at least one number.')

	if not has_symbol:
		raise ValueError('Password must contain at least one symbol.')

	return password


class Email(BaseModel):
	email: EmailStr


class Password(BaseModel):
	password: Annotated[str, AfterValidator(_validate_password)]


class UserLogin(Email, Password):
	pass


class UserCreateByPassword(Email, Password):
	pass


class _UserCreateBase(Email):
	name: str


class UserCreateByGitHub(_UserCreateBase):
	github_id: str


class UserCreateByGoogle(_UserCreateBase):
	google_id: str
