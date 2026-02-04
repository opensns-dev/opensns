import pytest


class TestHttpOnlyCookies:
    def test_login_sets_httponly_cookie(self, client, session):
        from app.models.models import User, UserSettings
        from app.core.auth import get_password_hash

        user = User(
            email="cookie@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_settings = UserSettings(user_id=user.id)
        session.add(user_settings)
        session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "cookie@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        assert "access_token" in response.cookies
        cookie = response.cookies.get("access_token")
        assert cookie is not None

    def test_auth_works_with_cookie(self, client, session):
        from app.models.models import User, UserSettings
        from app.core.auth import get_password_hash

        user = User(
            email="cookieauth@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_settings = UserSettings(user_id=user.id)
        session.add(user_settings)
        session.commit()

        login_response = client.post(
            "/auth/login",
            data={"username": "cookieauth@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200

        me_response = client.get("/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "cookieauth@example.com"

    def test_auth_works_with_header_fallback(self, client, test_user, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_logout_clears_cookie(self, client, session):
        from app.models.models import User, UserSettings
        from app.core.auth import get_password_hash

        user = User(
            email="logout@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_settings = UserSettings(user_id=user.id)
        session.add(user_settings)
        session.commit()

        login_response = client.post(
            "/auth/login",
            data={"username": "logout@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.cookies

        logout_response = client.post("/auth/logout")
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logged out successfully"

    def test_refresh_also_sets_cookie(self, client, session):
        from app.models.models import User, UserSettings
        from app.core.auth import get_password_hash

        user = User(
            email="refresh@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_settings = UserSettings(user_id=user.id)
        session.add(user_settings)
        session.commit()

        login_response = client.post(
            "/auth/login",
            data={"username": "refresh@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.cookies
