import base64
import json
from logging import getLogger
from typing import Any
from cryptography.fernet import Fernet

from app.misc.settings import settings

logger = getLogger(__name__)

master_key_bytes = base64.urlsafe_b64decode(settings.encryption_key)
if len(master_key_bytes) != 32:
	raise ValueError('ENCRYPTION_KEY must be a valid 32-byte key')
_fernet_instance = Fernet(settings.encryption_key.encode())


def encrypt(data: Any) -> str:
	try:
		payload = json.dumps({'data': data}).encode('utf-8')
		encrypted_bytes = _fernet_instance.encrypt(payload)
		return encrypted_bytes.decode('ascii')
	except Exception as e:
		logger.error(f'Encryption failed: {str(e)}')
		raise ValueError('Failed to encrypt data') from e


def decrypt(encrypted_data: str) -> Any:
	try:
		decrypted_bytes = _fernet_instance.decrypt(encrypted_data.encode())
		payload = json.loads(decrypted_bytes.decode('utf-8'))
		return payload['data']
	except json.JSONDecodeError as e:
		logger.error(f'Corrupted payload structure: {str(e)}')
		raise ValueError('Corrupted encrypted data') from e
	except Exception as e:
		logger.error(f'Decryption failed: {str(e)}')
		raise ValueError('Failed to decrypt data') from e
