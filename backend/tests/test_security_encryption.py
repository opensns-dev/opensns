import pytest
import os


class TestSecurityEncryption:
    def test_encryption_uses_unique_salt(self):
        from app.core.encryption import encrypt_api_key
        from app.core.config import settings

        plaintext = "sk-test-api-key-12345"
        enc1 = encrypt_api_key(plaintext, settings.API_KEY_ENCRYPTION_KEY)
        enc2 = encrypt_api_key(plaintext, settings.API_KEY_ENCRYPTION_KEY)

        assert enc1 != enc2

    def test_same_plaintext_different_ciphertext(self):
        from app.core.encryption import encrypt_api_key
        from app.core.config import settings

        plaintext = "same-api-key"
        encrypted_values = set()
        for _ in range(5):
            encrypted = encrypt_api_key(plaintext, settings.API_KEY_ENCRYPTION_KEY)
            encrypted_values.add(encrypted)

        assert len(encrypted_values) == 5

    def test_decryption_works_correctly(self):
        from app.core.encryption import encrypt_api_key, decrypt_api_key
        from app.core.config import settings

        plaintext = "sk-my-super-secret-key"
        encrypted = encrypt_api_key(plaintext, settings.API_KEY_ENCRYPTION_KEY)
        decrypted = decrypt_api_key(encrypted, settings.API_KEY_ENCRYPTION_KEY)

        assert decrypted == plaintext

    def test_encrypted_format_contains_version(self):
        from app.core.encryption import encrypt_api_key
        from app.core.config import settings

        plaintext = "test-key"
        encrypted = encrypt_api_key(plaintext, settings.API_KEY_ENCRYPTION_KEY)

        assert encrypted.startswith("v2:")

    def test_backward_compatibility_v1_format(self):
        from app.core.encryption import decrypt_api_key, _encrypt_v1
        from app.core.config import settings

        plaintext = "old-api-key-format"
        v1_encrypted = _encrypt_v1(plaintext, settings.API_KEY_ENCRYPTION_KEY)

        assert not v1_encrypted.startswith("v2:")

        decrypted = decrypt_api_key(v1_encrypted, settings.API_KEY_ENCRYPTION_KEY)
        assert decrypted == plaintext

    def test_pbkdf2_iterations_minimum(self):
        from app.core.encryption import PBKDF2_ITERATIONS

        assert PBKDF2_ITERATIONS >= 100000
