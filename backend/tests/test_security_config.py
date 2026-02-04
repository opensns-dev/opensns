import os
import sys
import pytest
from unittest.mock import patch


def _clear_config_module():
    modules_to_remove = [k for k in sys.modules.keys() if "app.core" in k]
    for mod in modules_to_remove:
        del sys.modules[mod]


class TestSecurityConfig:
    def test_startup_fails_with_placeholder_jwt_secret(self):
        _clear_config_module()

        env_with_placeholder = {
            "DATABASE_URL": "sqlite:///./test.db",
            "JWT_SECRET_KEY": "your-super-secret-key-change-in-production",
            "API_KEY_ENCRYPTION_KEY": "a-valid-32-character-key-here!!!",
        }

        with patch.dict(os.environ, env_with_placeholder, clear=True):
            from pydantic import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                _clear_config_module()
                from app.core.config import Settings

                Settings(_env_file=None)

            error_str = str(exc_info.value)
            assert (
                "change-in-production" in error_str or "your-super-secret" in error_str
            )

    def test_startup_fails_with_placeholder_encryption_key(self):
        _clear_config_module()

        env_with_placeholder = {
            "DATABASE_URL": "sqlite:///./test.db",
            "JWT_SECRET_KEY": "a-valid-32-character-jwt-secret!",
            "API_KEY_ENCRYPTION_KEY": "default-encryption-key-change-in-production",
        }

        with patch.dict(os.environ, env_with_placeholder, clear=True):
            from pydantic import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                _clear_config_module()
                from app.core.config import Settings

                Settings(_env_file=None)

            error_str = str(exc_info.value)
            assert (
                "change-in-production" in error_str or "default-encryption" in error_str
            )

    def test_startup_fails_with_short_jwt_secret(self):
        _clear_config_module()

        env_with_short_key = {
            "DATABASE_URL": "sqlite:///./test.db",
            "JWT_SECRET_KEY": "too-short",
            "API_KEY_ENCRYPTION_KEY": "a-valid-32-character-key-here!!!",
        }

        with patch.dict(os.environ, env_with_short_key, clear=True):
            from pydantic import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                _clear_config_module()
                from app.core.config import Settings

                Settings(_env_file=None)

            error_str = str(exc_info.value)
            assert "32" in error_str or "characters" in error_str.lower()

    def test_startup_fails_without_jwt_secret(self):
        _clear_config_module()

        env_without_jwt = {
            "DATABASE_URL": "sqlite:///./test.db",
            "API_KEY_ENCRYPTION_KEY": "a-valid-32-character-key-here!!!",
        }

        with patch.dict(os.environ, env_without_jwt, clear=True):
            from pydantic import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                _clear_config_module()
                from app.core.config import Settings

                Settings(_env_file=None)

            error_str = str(exc_info.value)
            assert "jwt_secret_key" in error_str.lower()

    def test_startup_fails_without_encryption_key(self):
        _clear_config_module()

        env_without_encryption = {
            "DATABASE_URL": "sqlite:///./test.db",
            "JWT_SECRET_KEY": "a-valid-32-character-jwt-secret!",
        }

        with patch.dict(os.environ, env_without_encryption, clear=True):
            from pydantic import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                _clear_config_module()
                from app.core.config import Settings

                Settings(_env_file=None)

            error_str = str(exc_info.value)
            assert "api_key_encryption_key" in error_str.lower()

    def test_startup_succeeds_with_valid_secrets(self):
        _clear_config_module()

        valid_env = {
            "DATABASE_URL": "sqlite:///./test.db",
            "JWT_SECRET_KEY": "a-valid-32-character-jwt-secret!",
            "API_KEY_ENCRYPTION_KEY": "a-valid-32-character-key-here!!!",
        }

        with patch.dict(os.environ, valid_env, clear=True):
            _clear_config_module()
            from app.core.config import Settings

            settings = Settings(_env_file=None)

            assert settings.JWT_SECRET_KEY == "a-valid-32-character-jwt-secret!"
            assert settings.API_KEY_ENCRYPTION_KEY == "a-valid-32-character-key-here!!!"
