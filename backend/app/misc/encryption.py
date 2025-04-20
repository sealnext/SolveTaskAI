import base64
import json
from logging import getLogger
from typing import Any
from cryptography.fernet import Fernet
from app.misc.settings import settings


class Encryption:
	"""
	Secure encryption service using Fernet symmetric encryption.
	Provides authenticated encryption to protect data integrity.
	"""

	def __init__(self) -> None:
		"""Initialize encryption service with the master key."""
		self.logger = getLogger(__name__)
		master_key_bytes = base64.urlsafe_b64decode(settings.encryption_key)
		if len(master_key_bytes) != 32:
			raise ValueError('ENCRYPTION_KEY must be a valid 32-byte key')
		self._fernet_instance = Fernet(settings.encryption_key.encode())
		self.logger.info('Encryption service initialized successfully')

	def encrypt(self, data: Any) -> str:
		"""
		Encrypt data using authenticated encryption.

		Args:
		    data: Data to encrypt (will be JSON serialized)

		Returns:
		    str: Encrypted data token (URL-safe base64 string)

		Raises:
		    ValueError: If encryption process fails
		"""
		try:
			payload = json.dumps({'data': data}).encode('utf-8')
			encrypted_bytes = self._fernet_instance.encrypt(payload)
			return encrypted_bytes.decode('ascii')

		except Exception as e:
			self.logger.error(f'Encryption failed: {str(e)}')
			raise ValueError('Failed to encrypt data') from e

	def decrypt(self, encrypted_data: str) -> Any:
		"""
		Decrypt data using authenticated decryption.

		Args:
		    encrypted_data: Encrypted data token (URL-safe base64 string)

		Returns:
		    Any: Original decrypted data

		Raises:
		    ValueError: If decryption fails or data is corrupted
		"""
		try:
			decrypted_bytes = self._fernet_instance.decrypt(encrypted_data.encode())
			payload = json.loads(decrypted_bytes.decode('utf-8'))
			return payload['data']

		except json.JSONDecodeError as e:
			self.logger.error(f'Corrupted payload structure: {str(e)}')
			raise ValueError('Corrupted encrypted data') from e

		except Exception as e:
			self.logger.error(f'Decryption failed: {str(e)}')
			raise ValueError('Failed to decrypt data') from e
