import pytest
from unittest.mock import patch, MagicMock


class TestWebSocketAuthentication:
    def test_websocket_rejects_missing_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/logs/1"):
                pass

    def test_websocket_rejects_invalid_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/logs/1?token=invalid-token"):
                pass

    def test_websocket_accepts_valid_token(
        self, client, test_user, auth_headers, session
    ):
        from app.models.models import Campaign

        campaign = Campaign(
            user_id=test_user.id,
            title="Test Campaign",
            product_url="https://example.com",
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        token = auth_headers["Authorization"].replace("Bearer ", "")
        with client.websocket_connect(
            f"/ws/logs/{campaign.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_rejects_other_users_campaign(self, client, session):
        from app.models.models import User, Campaign, UserSettings
        from app.core.auth import get_password_hash, create_access_token

        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user1)
        session.commit()
        session.refresh(user1)

        user1_settings = UserSettings(user_id=user1.id)
        session.add(user1_settings)

        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
            auth_provider="email",
        )
        session.add(user2)
        session.commit()
        session.refresh(user2)

        user2_settings = UserSettings(user_id=user2.id)
        session.add(user2_settings)

        campaign = Campaign(
            user_id=user1.id,
            title="User1's Campaign",
            product_url="https://example.com",
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        user2_token = create_access_token(data={"sub": str(user2.id)})

        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/ws/logs/{campaign.id}?token={user2_token}"
            ):
                pass

    def test_websocket_allows_own_campaign(
        self, client, test_user, auth_headers, session
    ):
        from app.models.models import Campaign

        campaign = Campaign(
            user_id=test_user.id,
            title="Owner's Campaign",
            product_url="https://example.com",
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        token = auth_headers["Authorization"].replace("Bearer ", "")

        with client.websocket_connect(
            f"/ws/logs/{campaign.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["campaign_id"] == campaign.id
