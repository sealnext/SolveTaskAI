import json
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256
from jose import jwe
import logging
from config import NEXTAUTH_SECRET 
import bcrypt

logger = logging.getLogger(__name__)

# Derive the encryption key using HKDF (as per the NextAuth.js key generation method)
def get_derived_encryption_key(secret: str) -> bytes:
    context = str.encode("NextAuth.js Generated Encryption Key")
    return HKDF(
        master=secret.encode(),
        key_len=32,
        salt=b"",
        hashmod=SHA256,
        num_keys=1,
        context=context
    )

# Decode and decrypt the NextAuth token
def decode_next_auth_token(token: str) -> dict:
    try:
        encryption_key = get_derived_encryption_key(NEXTAUTH_SECRET)
        decrypted_payload = jwe.decrypt(token, encryption_key).decode()
        payload = json.loads(decrypted_payload)
        return payload

    except Exception as e:
        logger.error(f"Failed to decode token: {e}")
        raise ValueError(f"Invalid key or token decryption failed: {e}")


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)
