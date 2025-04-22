from hashlib import blake2b
from secrets import token_urlsafe

from brevo_python import SendSmtpEmailTo
from fastapi import BackgroundTasks

from app.dto.user import UserCreateByPassword, UserLogin
from app.misc.crypto import password_hasher
from app.misc.email import (
	EmailVerification,
	email_verification_template_html,
	email_verification_template_text,
)
from app.misc.exception import SessionNotFoundException
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

	async def login(self, user_dto: UserLogin) -> str:
		user = await self.user_service.get_user_by_email(user_dto)
		password_hasher.verify(user.hashed_password, user_dto.password)
		session_token: str = await AuthService._create_session(user.id)
		return session_token

	async def register(
		self, user_dto: UserCreateByPassword, background_tasks: BackgroundTasks
	) -> None:
		user = await self.user_service.create_user_by_password(user_dto)

		email_verification_token = token_urlsafe(settings.email_verification_token_length)
		await redis.set(
			name=f'email_verification:{email_verification_token}',
			value=user.id,
			ex=settings.email_verification_ttl,
		)
		url = f'{settings.origin_url}/auth/verify-email?token={email_verification_token}'

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
