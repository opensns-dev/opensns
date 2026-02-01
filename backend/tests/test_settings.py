"""
Tests for settings endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import User, UserSettings


class TestGetSettings:
    """Tests for GET /settings"""

    def test_get_settings_default(self, client: TestClient, auth_headers: dict):
        """Test getting settings returns defaults."""
        response = client.get("/settings/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["default_llm_engine"] == "openai"
        assert data["default_image_engine"] == "fal"
        assert data["default_video_engine"] == "fal-video"
        assert data["has_openai_key"] is False
        assert data["has_fal_key"] is False

    def test_get_settings_unauthenticated(self, client: TestClient):
        """Test getting settings without auth fails."""
        response = client.get("/settings/")
        assert response.status_code == 401


class TestUpdateSettings:
    """Tests for PUT /settings"""

    def test_update_engine_preferences(self, client: TestClient, auth_headers: dict):
        """Test updating engine preferences."""
        response = client.put(
            "/settings/",
            headers=auth_headers,
            json={
                "default_llm_engine": "ollama",
                "default_image_engine": "comfyui",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["default_llm_engine"] == "ollama"
        assert data["default_image_engine"] == "comfyui"

    def test_update_local_urls(self, client: TestClient, auth_headers: dict):
        """Test updating local engine URLs."""
        response = client.put(
            "/settings/",
            headers=auth_headers,
            json={
                "ollama_url": "http://localhost:11434",
                "comfyui_url": "http://localhost:8188",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ollama_url"] == "http://localhost:11434"
        assert data["comfyui_url"] == "http://localhost:8188"

    def test_update_api_key_encrypted(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        """Test that API keys are stored encrypted."""
        response = client.put(
            "/settings/",
            headers=auth_headers,
            json={"openai_api_key": "sk-test-key-12345"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_openai_key"] is True

        # Verify key is encrypted in database
        user_settings = session.get(UserSettings, test_user.id)
        assert user_settings.openai_api_key != "sk-test-key-12345"
        assert user_settings.openai_api_key is not None

    def test_update_fal_api_key(self, client: TestClient, auth_headers: dict):
        """Test updating Fal.ai API key."""
        response = client.put(
            "/settings/",
            headers=auth_headers,
            json={"fal_api_key": "fal-test-key-67890"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_fal_key"] is True

    def test_update_settings_partial(self, client: TestClient, auth_headers: dict):
        """Test partial update only changes specified fields."""
        # First set some values
        client.put(
            "/settings/",
            headers=auth_headers,
            json={
                "default_llm_engine": "ollama",
                "ollama_url": "http://localhost:11434",
            },
        )

        # Update only one field
        response = client.put(
            "/settings/",
            headers=auth_headers,
            json={"default_image_engine": "comfyui"},
        )
        assert response.status_code == 200
        data = response.json()
        # Previous values should be preserved
        assert data["default_llm_engine"] == "ollama"
        assert data["ollama_url"] == "http://localhost:11434"
        # New value should be updated
        assert data["default_image_engine"] == "comfyui"

    def test_update_settings_unauthenticated(self, client: TestClient):
        """Test updating settings without auth fails."""
        response = client.put(
            "/settings/",
            json={"default_llm_engine": "ollama"},
        )
        assert response.status_code == 401


class TestTestConnection:
    """Tests for POST /settings/test-connection"""

    def test_test_connection_no_keys(self, client: TestClient, auth_headers: dict):
        """Test connection test with no keys configured."""
        response = client.post("/settings/test-connection", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["openai"] is False
        assert data["fal"] is False

    def test_test_connection_unauthenticated(self, client: TestClient):
        """Test connection test without auth fails."""
        response = client.post("/settings/test-connection")
        assert response.status_code == 401
