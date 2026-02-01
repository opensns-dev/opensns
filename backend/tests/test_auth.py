"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import User


class TestRegister:
    """Tests for POST /auth/register"""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "securepassword123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email fails."""
        response = client.post(
            "/auth/register",
            json={"email": test_user.email, "password": "anotherpassword"},
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={"email": "notanemail", "password": "password123"},
        )
        # FastAPI/Pydantic validation - should still accept as string
        # since we're not using EmailStr
        assert response.status_code in [201, 422]

    def test_register_missing_password(self, client: TestClient):
        """Test registration without password fails."""
        response = client.post(
            "/auth/register",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login returns token."""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password fails."""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user fails."""
        response = client.post(
            "/auth/login",
            data={"username": "noone@example.com", "password": "password"},
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, session: Session):
        """Test login with inactive user fails."""
        from app.core.auth import get_password_hash

        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        session.add(inactive_user)
        session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "inactive@example.com", "password": "password123"},
        )
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestMe:
    """Tests for GET /auth/me"""

    def test_me_authenticated(
        self, client: TestClient, auth_headers: dict, test_user: User
    ):
        """Test getting current user when authenticated."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    def test_me_unauthenticated(self, client: TestClient):
        """Test getting current user without token fails."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
