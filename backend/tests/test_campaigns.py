"""
Tests for campaign endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from unittest.mock import patch

from app.models.models import User, Campaign, CampaignStatus


class TestListCampaigns:
    """Tests for GET /campaigns"""

    def test_list_campaigns_empty(self, client: TestClient, auth_headers: dict):
        """Test listing campaigns when user has none."""
        response = client.get("/campaigns/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_campaigns_with_data(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        """Test listing campaigns returns user's campaigns."""
        # Create campaigns for the test user
        campaign1 = Campaign(
            title="Test Campaign 1",
            product_url="https://example.com/product1",
            user_id=test_user.id,
        )
        campaign2 = Campaign(
            title="Test Campaign 2",
            product_url="https://example.com/product2",
            user_id=test_user.id,
        )
        session.add(campaign1)
        session.add(campaign2)
        session.commit()

        response = client.get("/campaigns/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = [c["title"] for c in data]
        assert "Test Campaign 1" in titles
        assert "Test Campaign 2" in titles

    def test_list_campaigns_only_own(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        """Test that users only see their own campaigns."""
        # Create another user with a campaign
        from app.core.auth import get_password_hash

        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        other_campaign = Campaign(
            title="Other's Campaign",
            product_url="https://example.com/other",
            user_id=other_user.id,
        )
        session.add(other_campaign)
        session.commit()

        # Current user should not see other's campaign
        response = client.get("/campaigns/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_campaigns_unauthenticated(self, client: TestClient):
        """Test listing campaigns without auth fails."""
        response = client.get("/campaigns/")
        assert response.status_code == 401


class TestCreateCampaign:
    """Tests for POST /campaigns"""

    @patch("app.api.campaigns.run_campaign_pipeline")
    def test_create_campaign_success(
        self, mock_pipeline, client: TestClient, auth_headers: dict
    ):
        """Test successful campaign creation."""
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={
                "title": "New Campaign",
                "product_url": "https://example.com/product",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Campaign"
        assert data["product_url"] == "https://example.com/product"
        assert data["status"] == "PENDING"
        assert "id" in data

    @patch("app.api.campaigns.run_campaign_pipeline")
    def test_create_campaign_with_description(
        self, mock_pipeline, client: TestClient, auth_headers: dict
    ):
        """Test campaign creation with description."""
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={
                "title": "Described Campaign",
                "product_url": "https://example.com/product",
                "description": "A detailed description of the campaign",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "A detailed description of the campaign"

    def test_create_campaign_missing_title(
        self, client: TestClient, auth_headers: dict
    ):
        """Test campaign creation without title fails."""
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={"product_url": "https://example.com/product"},
        )
        assert response.status_code == 422

    def test_create_campaign_missing_url(self, client: TestClient, auth_headers: dict):
        """Test campaign creation without URL fails."""
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={"title": "No URL Campaign"},
        )
        assert response.status_code == 422

    def test_create_campaign_unauthenticated(self, client: TestClient):
        """Test campaign creation without auth fails."""
        response = client.post(
            "/campaigns/",
            json={
                "title": "Unauthorized Campaign",
                "product_url": "https://example.com/product",
            },
        )
        assert response.status_code == 401


class TestGetCampaign:
    """Tests for GET /campaigns/{id}"""

    def test_get_campaign_success(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        """Test getting a specific campaign."""
        campaign = Campaign(
            title="Specific Campaign",
            product_url="https://example.com/specific",
            user_id=test_user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.get(f"/campaigns/{campaign.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign.id
        assert data["title"] == "Specific Campaign"

    def test_get_campaign_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent campaign returns 404."""
        response = client.get("/campaigns/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_campaign_other_user(
        self, client: TestClient, auth_headers: dict, session: Session
    ):
        """Test getting another user's campaign returns 404."""
        from app.core.auth import get_password_hash

        other_user = User(
            email="other2@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        other_campaign = Campaign(
            title="Private Campaign",
            product_url="https://example.com/private",
            user_id=other_user.id,
        )
        session.add(other_campaign)
        session.commit()
        session.refresh(other_campaign)

        response = client.get(f"/campaigns/{other_campaign.id}", headers=auth_headers)
        assert response.status_code == 404


class TestApproveCampaign:
    """Tests for POST /campaigns/{id}/approve"""

    @patch("app.api.campaigns.approve_and_resume")
    def test_approve_campaign_success(
        self,
        mock_resume,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
    ):
        """Test approving a campaign awaiting approval."""
        campaign = Campaign(
            title="Awaiting Campaign",
            product_url="https://example.com/awaiting",
            user_id=test_user.id,
            status=CampaignStatus.AWAITING_APPROVAL,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.post(
            f"/campaigns/{campaign.id}/approve", headers=auth_headers
        )
        assert response.status_code == 200

    def test_approve_campaign_wrong_status(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        """Test approving a campaign not awaiting approval fails."""
        campaign = Campaign(
            title="Pending Campaign",
            product_url="https://example.com/pending",
            user_id=test_user.id,
            status=CampaignStatus.PENDING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.post(
            f"/campaigns/{campaign.id}/approve", headers=auth_headers
        )
        assert response.status_code == 400
        assert "not awaiting approval" in response.json()["detail"].lower()
