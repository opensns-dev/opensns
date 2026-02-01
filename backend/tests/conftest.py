"""
Pytest fixtures for OpenSNS backend tests.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db import get_session
from app.models.models import User, UserSettings
from app.core.auth import get_password_hash, create_access_token


# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create user settings
    settings = UserSettings(user_id=user.id)
    session.add(settings)
    session.commit()

    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User) -> dict:
    """Create authorization headers with a valid JWT token."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="authenticated_client")
def authenticated_client_fixture(
    client: TestClient, auth_headers: dict
) -> tuple[TestClient, dict]:
    """Return client with auth headers for convenience."""
    return client, auth_headers
