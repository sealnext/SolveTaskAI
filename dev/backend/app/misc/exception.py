class BaseCustomException(Exception):
	pass


class UserAlreadyExistsException(BaseCustomException):
	pass


class SessionNotFoundException(BaseCustomException):
	pass
