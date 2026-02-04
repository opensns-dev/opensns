import pytest
from datetime import datetime, timezone, timedelta


class TestRefreshTokens:
    def test_login_returns_refresh_token(self, client, test_user):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] is not None

    def test_refresh_endpoint_returns_new_tokens(self, client, test_user):
        login_response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token

    def test_refresh_token_cannot_be_reused(self, client, test_user):
        login_response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        first_refresh = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert first_refresh.status_code == 200

        second_refresh = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert second_refresh.status_code == 401
        assert "revoked" in second_refresh.json()["detail"].lower()

    def test_refresh_rejects_invalid_token(self, client):
        response = client.post(
            "/auth/refresh",
            params={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_rejects_expired_token(self, client, test_user, session):
        from app.models.models import RefreshToken

        login_response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        from sqlmodel import select

        token_obj = session.exec(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        ).first()
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.add(token_obj)
        session.commit()

        response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_access_token_works_after_refresh(self, client, test_user):
        login_response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        new_access_token = refresh_response.json()["access_token"]

        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "test@example.com"
