import os
from base64 import b64decode, b64encode

from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.misc.settings import settings

password_hasher = PasswordHasher()

_cipher = AESGCM(settings.encryption_key.get_secret_value())


def encrypt_raw(data: bytes) -> bytes:
	nonce: bytes = os.urandom(12)
	encrypted_data: bytes = _cipher.encrypt(nonce, data, None)
	return nonce + encrypted_data


def encrypt(data: str) -> str:
	return b64encode(encrypt_raw(data.encode())).decode('ascii')


def decrypt_raw(encrypted_data: bytes) -> bytes:
	nonce = encrypted_data[:12]
	encrypted = encrypted_data[12:]
	decrypted: bytes = _cipher.decrypt(nonce, encrypted, None)
	return decrypted


def decrypt(encrypted_data: str) -> str:
	return decrypt_raw(b64decode(encrypted_data.encode('ascii'))).decode()
