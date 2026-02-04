import os
import sys
import time
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestOAuthStateValidation:
    @pytest.fixture(autouse=True)
    def patch_google_settings(self):
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-client-secret"
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
            yield mock_settings

    def test_google_login_returns_state(self, client):
        response = client.get("/auth/google")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert len(data["state"]) >= 32

    def test_callback_rejects_missing_state(self, client):
        response = client.post("/auth/google/callback", params={"code": "test-code"})
        assert response.status_code == 422

    def test_callback_rejects_invalid_state(self, client):
        response = client.post(
            "/auth/google/callback",
            params={"code": "test-code", "state": "invalid-state-token"},
        )
        assert response.status_code == 400
        assert (
            "invalid" in response.json()["detail"].lower()
            or "state" in response.json()["detail"].lower()
        )

    def test_callback_rejects_expired_state(self, client):
        from app.api.auth import oauth_state_store, OAUTH_STATE_EXPIRY_SECONDS

        expired_state = "expired-state-token"
        oauth_state_store[expired_state] = time.time() - OAUTH_STATE_EXPIRY_SECONDS - 1

        response = client.post(
            "/auth/google/callback",
            params={"code": "test-code", "state": expired_state},
        )
        assert response.status_code == 400
        assert (
            "expired" in response.json()["detail"].lower()
            or "state" in response.json()["detail"].lower()
        )

    def test_callback_accepts_valid_state(self, client):
        login_response = client.get("/auth/google")
        assert login_response.status_code == 200
        state = login_response.json()["state"]

        with patch("app.api.auth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_instance.post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"access_token": "google-access-token"},
            )
            mock_instance.get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"id": "google-123", "email": "test@example.com"},
            )

            response = client.post(
                "/auth/google/callback",
                params={"code": "valid-code", "state": state},
            )

            assert response.status_code == 200
            assert "access_token" in response.json()

    def test_state_cannot_be_reused(self, client):
        login_response = client.get("/auth/google")
        state = login_response.json()["state"]

        with patch("app.api.auth.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_instance.post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"access_token": "google-access-token"},
            )
            mock_instance.get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"id": "google-456", "email": "test2@example.com"},
            )

            first_response = client.post(
                "/auth/google/callback",
                params={"code": "valid-code", "state": state},
            )
            assert first_response.status_code == 200

        second_response = client.post(
            "/auth/google/callback",
            params={"code": "valid-code", "state": state},
        )
        assert second_response.status_code == 400
