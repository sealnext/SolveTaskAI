import os
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.misc.settings import settings


password_hasher = PasswordHasher()

_cipher = AESGCM(settings.encryption_key.get_secret_value())


def encrypt(data: bytes) -> bytes:
	nonce: bytes = os.urandom(12)
	encrypted_data: bytes = _cipher.encrypt(nonce, data, None)
	return nonce + encrypted_data


def decrypt(encrypted_data: bytes) -> bytes:
	nonce = encrypted_data[:12]
	encrypted = encrypted_data[12:]
	decrypted: bytes = _cipher.decrypt(nonce, encrypted, None)
	return decrypted
