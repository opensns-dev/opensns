"""
Tests for account lockout after failed login attempts.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import User, UserSettings, utc_now
from app.core.auth import get_password_hash
from app.api.auth import MAX_FAILED_LOGIN_ATTEMPTS, ACCOUNT_LOCKOUT_MINUTES


@pytest.fixture(name="lockout_user")
def lockout_user_fixture(session: Session) -> User:
    user = User(
        email="lockout@example.com",
        hashed_password=get_password_hash("correctpassword"),
        is_active=True,
        is_verified=True,
        auth_provider="email",
        failed_login_attempts=0,
        locked_until=None,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    settings = UserSettings(user_id=user.id)
    session.add(settings)
    session.commit()

    return user


def test_failed_login_increments_counter(
    client: TestClient, session: Session, lockout_user: User
):
    response = client.post(
        "/auth/login",
        data={"username": "lockout@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401

    session.refresh(lockout_user)
    assert lockout_user.failed_login_attempts == 1


def test_successful_login_resets_counter(
    client: TestClient, session: Session, lockout_user: User
):
    lockout_user.failed_login_attempts = 3
    session.add(lockout_user)
    session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "lockout@example.com", "password": "correctpassword"},
    )
    assert response.status_code == 200

    session.refresh(lockout_user)
    assert lockout_user.failed_login_attempts == 0
    assert lockout_user.locked_until is None


def test_account_locks_after_max_attempts(
    client: TestClient, session: Session, lockout_user: User
):
    for i in range(MAX_FAILED_LOGIN_ATTEMPTS):
        response = client.post(
            "/auth/login",
            data={"username": "lockout@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    session.refresh(lockout_user)
    assert lockout_user.failed_login_attempts == MAX_FAILED_LOGIN_ATTEMPTS
    assert lockout_user.locked_until is not None


def test_locked_account_rejects_login(
    client: TestClient, session: Session, lockout_user: User
):
    lockout_user.failed_login_attempts = MAX_FAILED_LOGIN_ATTEMPTS
    lockout_user.locked_until = utc_now() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
    session.add(lockout_user)
    session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "lockout@example.com", "password": "correctpassword"},
    )
    assert response.status_code == 403
    assert "temporarily locked" in response.json()["detail"]


def test_expired_lockout_allows_login(
    client: TestClient, session: Session, lockout_user: User
):
    lockout_user.failed_login_attempts = MAX_FAILED_LOGIN_ATTEMPTS
    lockout_user.locked_until = utc_now() - timedelta(minutes=1)
    session.add(lockout_user)
    session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "lockout@example.com", "password": "correctpassword"},
    )
    assert response.status_code == 200

    session.refresh(lockout_user)
    assert lockout_user.failed_login_attempts == 0
    assert lockout_user.locked_until is None


def test_generic_error_message_hides_user_existence(client: TestClient):
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
