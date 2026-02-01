from cryptography.fernet import Fernet
import base64
import hashlib


def get_fernet(key: str) -> Fernet:
    key_bytes = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_api_key(api_key: str, encryption_key: str) -> str:
    f = get_fernet(encryption_key)
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str, encryption_key: str) -> str:
    f = get_fernet(encryption_key)
    return f.decrypt(encrypted_key.encode()).decode()
