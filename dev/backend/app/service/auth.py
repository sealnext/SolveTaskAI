from hashlib import blake2b
from secrets import token_urlsafe
from urllib.parse import urljoin

from brevo_python import SendSmtpEmailTo
from fastapi import BackgroundTasks

from app.dto.user import UserCreateByPassword, UserLogin, UserPublic
from app.misc.crypto import password_hasher
from app.misc.email import (
	EmailVerification,
	email_verification_template_html,
	email_verification_template_text,
)
from app.misc.exception import SessionNotFoundException, TokenNotFoundException
from app.misc.logger import logger
from app.misc.redis import redis
from app.misc.settings import settings
from app.service.user import UserService


class AuthService:
	def __init__(self, user_service: UserService):
		self.user_service = user_service

	@staticmethod
	async def _create_session(user_id: int) -> str:
		session_token: str = token_urlsafe(settings.session_token_length)
		session_id: str = blake2b(session_token.encode()).hexdigest()
		await redis.set(name=f'session:{session_id}', value=user_id, ex=settings.session_ttl)
		return session_token

	@staticmethod
	def get_session_id(session_token: str) -> str:
		session_id = blake2b(session_token.encode()).hexdigest()
		return session_id

	@staticmethod
	async def get_user_id(session_id: str) -> int:
		user_id_str: str | None = await redis.get(f'session:{session_id}')
		if user_id_str is None:
			raise SessionNotFoundException('Session not found')
		user_id = int(user_id_str)
		return user_id

	@staticmethod
	async def session_exists(session_id: str) -> bool:
		user_id_str: str | None = await redis.get(f'session:{session_id}')
		return user_id_str is not None

	async def login(self, user_dto: UserLogin) -> tuple[str, UserPublic]:
		user = await self.user_service.get_user_by_email(user_dto)
		password_hasher.verify(user.hashed_password, user_dto.password)
		session_token: str = await AuthService._create_session(user.id)
		user_public_dto = UserPublic(
			name=user.name, email=user.email, is_email_verified=user.is_email_verified
		)
		return session_token, user_public_dto

	async def logout(self, session_id: str) -> None:
		number_of_deleted_keys = await redis.delete(f'session:{session_id}')
		if number_of_deleted_keys == 0:
			logger.info('Session not found: %s', session_id)

	async def register(
		self, user_dto: UserCreateByPassword, background_tasks: BackgroundTasks
	) -> tuple[str, UserPublic]:
		user = await self.user_service.create_user_by_password(user_dto)

		email_verification_token = token_urlsafe(settings.email_verification_token_length)
		await redis.set(
			name=f'email_verification:{email_verification_token}',
			value=user.id,
			ex=settings.email_verification_ttl,
		)

		url: str = urljoin(
			str(settings.origin_url), f'/api/auth/verify-email?token={email_verification_token}'
		)

		verification_email_html = email_verification_template_html.render(
			email_verification_link=url
		)
		verification_email_text = email_verification_template_text.render(
			email_verification_link=url
		)

		email = EmailVerification(
			to=[SendSmtpEmailTo(email=user_dto.email)],
			html_content=verification_email_html,
			text_content=verification_email_text,
		)
		background_tasks.add_task(email.send)

		session_token: str = await AuthService._create_session(user.id)
		user_public_dto = UserPublic(
			name=None, email=user.email, is_email_verified=user.is_email_verified
		)
		return session_token, user_public_dto

	async def email_exists(self, email: str) -> bool:
		user = await self.user_service.get_user_by_email(email)
		return user is not None

	async def verify_email(self, token: str) -> None:
		user_id_str: str | None = await redis.get(f'email_verification:{token}')
		if user_id_str is None:
			raise TokenNotFoundException('Email verification token not found')

		await redis.delete(f'email_verification:{token}')

		user_id = int(user_id_str)
		await self.user_service.verify_email(user_id)
