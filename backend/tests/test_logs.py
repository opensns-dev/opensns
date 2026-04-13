"""
Tests for logs endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import AgentLog, Campaign, User
from app.core.auth import get_password_hash


class TestListLogs:
    """Tests for GET /logs/campaign/{campaign_id}"""

    def test_list_logs(self, client: TestClient, session: Session):
        """Test listing logs for a campaign."""
        # Create user and campaign
        user = User(
            email="logs_test@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Logs Test Campaign",
            product_url="https://example.com/product",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Create agent logs
        log1 = AgentLog(
            campaign_id=campaign.id,
            agent_name="research_agent",
            message="Started product research",
            level="INFO",
        )
        log2 = AgentLog(
            campaign_id=campaign.id,
            agent_name="copy_agent",
            message="Generated 3 copy variants",
            level="INFO",
        )
        log3 = AgentLog(
            campaign_id=campaign.id,
            agent_name="image_agent",
            message="Failed to generate image",
            level="ERROR",
        )
        session.add(log1)
        session.add(log2)
        session.add(log3)
        session.commit()

        response = client.get(f"/logs/campaign/{campaign.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        agents = [log["agent_name"] for log in data]
        assert "research_agent" in agents
        assert "copy_agent" in agents
        assert "image_agent" in agents
        levels = [log["level"] for log in data]
        assert "INFO" in levels
        assert "ERROR" in levels

    def test_list_logs_empty_campaign(self, client: TestClient, session: Session):
        """Test listing logs for campaign with no logs."""
        # Create user and campaign
        user = User(
            email="logs_empty@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Empty Logs Campaign",
            product_url="https://example.com/empty",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.get(f"/logs/campaign/{campaign.id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_logs_different_campaigns(self, client: TestClient, session: Session):
        """Test logs are separated by campaign."""
        # Create user
        user = User(
            email="logs_separate@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create two campaigns
        campaign1 = Campaign(
            title="Campaign One",
            product_url="https://example.com/one",
            user_id=user.id,
        )
        campaign2 = Campaign(
            title="Campaign Two",
            product_url="https://example.com/two",
            user_id=user.id,
        )
        session.add(campaign1)
        session.add(campaign2)
        session.commit()
        session.refresh(campaign1)
        session.refresh(campaign2)

        # Add logs to campaign1 only
        log1 = AgentLog(
            campaign_id=campaign1.id,
            agent_name="research_agent",
            message="Research for campaign 1",
            level="INFO",
        )
        session.add(log1)
        session.commit()

        # Check campaign1 has logs
        response = client.get(f"/logs/campaign/{campaign1.id}")
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Check campaign2 has no logs
        response = client.get(f"/logs/campaign/{campaign2.id}")
        assert response.status_code == 200
        assert response.json() == []
