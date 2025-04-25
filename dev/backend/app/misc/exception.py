class BaseCustomException(Exception):
	pass


class UserNotFoundException(BaseCustomException):
	pass


class SessionNotFoundException(BaseCustomException):
	pass


class TokenNotFoundException(BaseCustomException):
	pass
