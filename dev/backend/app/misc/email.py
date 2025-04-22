from dataclasses import dataclass
from venv import logger

from brevo_python import (
	ApiClient,
	Configuration,
	SendSmtpEmail,
	SendSmtpEmailReplyTo,
	SendSmtpEmailSender,
	SendSmtpEmailTo,
	TransactionalEmailsApi,
)
from brevo_python.rest import ApiException
from jinja2 import Environment, PackageLoader, select_autoescape

from app.misc.settings import settings

_jinja_env = Environment(
	loader=PackageLoader('app', 'email_template'), autoescape=select_autoescape()
)
# Templates
email_verification_template_html = _jinja_env.get_template('html/email_verification.html')
email_verification_template_text = _jinja_env.get_template('text/email_verification.txt')

# Brevo API Configuration
_brevo_configuration = Configuration()
_brevo_configuration.api_key['api-key'] = settings.email_api_key.get_secret_value()
_email_api = TransactionalEmailsApi(ApiClient(_brevo_configuration))


@dataclass
class Email:
	subject: str
	sender: SendSmtpEmailSender
	reply_to: SendSmtpEmailReplyTo
	html_content: str
	text_content: str
	to: list[SendSmtpEmailTo]
	tags: list[str]

	# Use this method always with fastapi.BackgroundTasks to avoid blocking the thread
	# Fire and forget
	def send(self):
		email = SendSmtpEmail(
			sender=self.sender,
			to=self.to,
			html_content=self.html_content,
			text_content=self.text_content,
			subject=self.subject,
			reply_to=self.reply_to,
			tags=self.tags,
		)
		try:
			result = _email_api.send_transac_email(email)
			logger.warning(f'Successfully sent email: {result}')
		except ApiException as e:
			logger.error(f'Exception when calling brevo SMTPApi->send_transac_email: {e}')
		except Exception as e:
			logger.error(f'Exception when sending email: {e}')


class EmailVerification(Email):
	def __init__(
		self,
		to: list[SendSmtpEmailTo],
		html_content: str,
		text_content: str,
		subject: str = 'Verify your email to activate your account',
		sender: SendSmtpEmailSender = SendSmtpEmailSender(
			name='SEALNEXT', email='noreply@sealnext.com'
		),
		reply_to: SendSmtpEmailReplyTo = SendSmtpEmailReplyTo(
			name='Sealnext Support', email='support@sealnext.com'
		),
		tags: list[str] = ['email_verification'],
	):
		super().__init__(subject, sender, reply_to, html_content, text_content, to, tags)
