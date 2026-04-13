"""
Tests for provider management endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.credential_resolver import dual_write_credential
from app.models.models import ProviderCredential, User


class TestProviderCredentials:
    """Tests for provider credential CRUD operations."""

    def test_save_url_only_provider(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
    ):
        """Test saving a URL-only provider (ComfyUI) with localhost address."""
        response = client.post(
            "/providers/credentials",
            headers=auth_headers,
            json={
                "provider_name": "comfyui",
                "endpoint_url": "http://127.0.0.1:8188",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "comfyui"
        assert data["endpoint_url"] == "http://127.0.0.1:8188"

        credential = session.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == test_user.id,
                ProviderCredential.provider_name == "comfyui",
            )
        ).first()
        assert credential is not None
        assert credential.endpoint_url == "http://127.0.0.1:8188"

    def test_save_url_only_provider_private_ip(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test saving a URL-only provider with private IP address."""
        response = client.post(
            "/providers/credentials",
            headers=auth_headers,
            json={
                "provider_name": "comfyui",
                "endpoint_url": "http://192.168.1.100:8188",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["endpoint_url"] == "http://192.168.1.100:8188"

    def test_update_existing_url_only_provider(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
    ):
        """Test updating an existing URL-only provider without duplicate entry issues."""
        assert test_user.id is not None
        dual_write_credential(
            session, test_user.id, "comfyui", endpoint_url="http://127.0.0.1:8188"
        )
        session.commit()

        response = client.post(
            "/providers/credentials",
            headers=auth_headers,
            json={
                "provider_name": "comfyui",
                "endpoint_url": "http://127.0.0.1:8288",
            },
        )
        assert response.status_code == 200
        assert response.json()["endpoint_url"] == "http://127.0.0.1:8288"

        credentials = session.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == test_user.id,
                ProviderCredential.provider_name == "comfyui",
            )
        ).all()
        assert len(credentials) == 1
        assert credentials[0].endpoint_url == "http://127.0.0.1:8288"

    def test_comfyui_video_uses_shared_url(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
        monkeypatch,
    ):
        """Test that comfyui-video test can use the URL stored under comfyui."""
        assert test_user.id is not None
        dual_write_credential(
            session, test_user.id, "comfyui", endpoint_url="http://127.0.0.1:8188"
        )
        session.commit()

        async def fake_test(provider_name: str, api_key: str, endpoint_url: str | None):
            from app.models.models import ProviderCredentialTestResult

            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=endpoint_url == "http://127.0.0.1:8188",
                message="ok",
            )

        monkeypatch.setattr("app.api.providers._test_provider_api", fake_test)

        response = client.post(
            "/providers/credentials/comfyui-video/test",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_save_provider_with_api_key(self, client: TestClient, byok_headers: dict):
        """Test saving a provider that requires an API key."""
        response = client.post(
            "/providers/credentials",
            headers=byok_headers,
            json={
                "provider_name": "openai",
                "credential_key": "sk-test-key",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "openai"
        assert data["has_credential_key"] is True

    def test_save_provider_missing_required_url(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that saving a URL-required provider without URL fails."""
        response = client.post(
            "/providers/credentials",
            headers=auth_headers,
            json={
                "provider_name": "comfyui",
            },
        )
        assert response.status_code == 400
        assert "requires an endpoint URL" in response.json()["detail"]

    def test_save_unknown_provider(self, client: TestClient, auth_headers: dict):
        """Test that saving an unknown provider fails."""
        response = client.post(
            "/providers/credentials",
            headers=auth_headers,
            json={
                "provider_name": "unknown-provider",
                "credential_key": "test-key",
            },
        )
        assert response.status_code == 400
        assert "Unknown provider" in response.json()["detail"]


class TestProviderConnectivityTest:
    """Tests for the connectivity test endpoint."""

    def test_connectivity_test_no_credential(
        self, client: TestClient, auth_headers: dict
    ):
        """Test connectivity check without saved credential."""
        response = client.post(
            "/providers/credentials/comfyui/test", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "comfyui"
        assert data["success"] is False
        assert "No credential found" in data["message"]

    def test_connectivity_test_with_url_only_provider(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
        monkeypatch,
    ):
        """Test connectivity check with URL-only provider."""
        assert test_user.id is not None
        dual_write_credential(
            session, test_user.id, "comfyui", endpoint_url="http://127.0.0.1:8188"
        )
        session.commit()

        async def fake_test(provider_name: str, api_key: str, endpoint_url: str | None):
            from app.models.models import ProviderCredentialTestResult

            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=True,
                message="Connected successfully",
            )

        monkeypatch.setattr("app.api.providers._test_provider_api", fake_test)

        response = client.post(
            "/providers/credentials/comfyui/test",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestProviderCompatibilityTest:
    """Tests for the compatibility test endpoint."""

    def test_compatibility_test_not_implemented(
        self, client: TestClient, auth_headers: dict
    ):
        """Test compatibility endpoint for non-implemented provider returns placeholder."""
        response = client.post(
            "/providers/credentials/openai/test-compatibility",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "openai"
        assert data["test_type"] == "compatibility"
        assert "not implemented" in data["message"].lower()
        assert data["capabilities"] == {}

    def test_compatibility_test_no_credential(
        self, client: TestClient, auth_headers: dict
    ):
        """Test compatibility check without saved credential."""
        response = client.post(
            "/providers/credentials/comfyui/test-compatibility",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "comfyui"
        assert data["success"] is False
        assert data["test_type"] == "compatibility"

    def test_compatibility_test_shared_url_provider(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
        monkeypatch,
    ):
        """Test that comfyui-video compatibility can use comfyui's URL."""
        assert test_user.id is not None
        dual_write_credential(
            session, test_user.id, "comfyui", endpoint_url="http://127.0.0.1:8188"
        )
        session.commit()

        import httpx

        class MockResponse:
            status_code = 200

            def json(self):
                return {
                    "CheckpointLoaderSimple": {},
                    "SaveImage": {},
                    "KSampler": {},
                }

        async def mock_get(*args, **kwargs):
            return MockResponse()

        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

        response = client.post(
            "/providers/credentials/comfyui-video/test-compatibility",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "comfyui-video"
        assert data["test_type"] == "compatibility"
        assert "capabilities" in data


class TestProviderRegistry:
    """Tests for the provider registry endpoint."""

    def test_get_registry(self, client: TestClient, auth_headers: dict):
        """Test getting provider registry returns all providers."""
        response = client.get("/providers/registry", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        provider_names = {p["name"] for p in data["providers"]}
        assert "openai" in provider_names
        assert "comfyui" in provider_names
        assert "comfyui-video" in provider_names
        assert "ollama" in provider_names

    def test_get_registry_filtered_by_type(
        self, client: TestClient, auth_headers: dict
    ):
        """Test filtering providers by type."""
        response = client.get(
            "/providers/registry?provider_type=image", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for provider in data["providers"]:
            assert provider["provider_type"] == "image"

    def test_get_registry_unauthenticated(self, client: TestClient):
        """Test getting registry without auth fails."""
        response = client.get("/providers/registry")
        assert response.status_code == 401
