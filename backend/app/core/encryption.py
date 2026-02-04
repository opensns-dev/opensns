from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib
import os

PBKDF2_ITERATIONS = 100000
SALT_LENGTH = 16


def _get_fernet_v1(key: str) -> Fernet:
    key_bytes = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def _encrypt_v1(api_key: str, encryption_key: str) -> str:
    f = _get_fernet_v1(encryption_key)
    return f.encrypt(api_key.encode()).decode()


def _decrypt_v1(encrypted_key: str, encryption_key: str) -> str:
    f = _get_fernet_v1(encryption_key)
    return f.decrypt(encrypted_key.encode()).decode()


def _derive_key_v2(encryption_key: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(encryption_key.encode())


def _get_fernet_v2(encryption_key: str, salt: bytes) -> Fernet:
    derived_key = _derive_key_v2(encryption_key, salt)
    return Fernet(base64.urlsafe_b64encode(derived_key))


def encrypt_api_key(api_key: str, encryption_key: str) -> str:
    salt = os.urandom(SALT_LENGTH)
    f = _get_fernet_v2(encryption_key, salt)
    encrypted = f.encrypt(api_key.encode())
    salt_b64 = base64.urlsafe_b64encode(salt).decode()
    encrypted_b64 = encrypted.decode()
    return f"v2:{salt_b64}:{encrypted_b64}"


def decrypt_api_key(encrypted_key: str, encryption_key: str) -> str:
    if encrypted_key.startswith("v2:"):
        parts = encrypted_key.split(":", 2)
        if len(parts) != 3:
            raise ValueError("Invalid v2 encrypted format")
        _, salt_b64, encrypted_b64 = parts
        salt = base64.urlsafe_b64decode(salt_b64)
        f = _get_fernet_v2(encryption_key, salt)
        return f.decrypt(encrypted_b64.encode()).decode()
    else:
        return _decrypt_v1(encrypted_key, encryption_key)
