"""
Tests for assets endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import Asset, AssetType, Campaign, User
from app.core.auth import get_password_hash


class TestListAssets:
    """Tests for GET /assets/campaign/{campaign_id}"""

    def test_list_assets_by_campaign(self, client: TestClient, session: Session):
        """Test listing assets by campaign returns all assets."""
        # Create user and campaign
        user = User(
            email="asset_test@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Asset Test Campaign",
            product_url="https://example.com/product",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Create assets of different types
        asset_copy = Asset(
            campaign_id=campaign.id,
            type=AssetType.COPY,
            content="Ad copy text here",
        )
        asset_image = Asset(
            campaign_id=campaign.id,
            type=AssetType.IMAGE,
            content="https://example.com/image.jpg",
            asset_metadata='{"width": 1024, "height": 1024}',
        )
        asset_video = Asset(
            campaign_id=campaign.id,
            type=AssetType.VIDEO,
            content="https://example.com/video.mp4",
            asset_metadata='{"duration": 30}',
        )
        session.add(asset_copy)
        session.add(asset_image)
        session.add(asset_video)
        session.commit()

        response = client.get(f"/assets/campaign/{campaign.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        types = [a["type"] for a in data]
        assert "COPY" in types
        assert "IMAGE" in types
        assert "VIDEO" in types

    def test_list_assets_empty_campaign(self, client: TestClient, session: Session):
        """Test listing assets for campaign with no assets."""
        # Create user and campaign
        user = User(
            email="asset_empty@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Empty Asset Campaign",
            product_url="https://example.com/empty",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.get(f"/assets/campaign/{campaign.id}")
        assert response.status_code == 200
        assert response.json() == []


class TestGetAsset:
    """Tests for GET /assets/{asset_id}"""

    def test_get_asset_success(self, client: TestClient, session: Session):
        """Test getting a specific asset."""
        # Create user, campaign, and asset
        user = User(
            email="asset_get@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Get Asset Campaign",
            product_url="https://example.com/get",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        asset = Asset(
            campaign_id=campaign.id,
            type=AssetType.IMAGE,
            content="https://example.com/specific-image.jpg",
            asset_metadata='{"width": 1024}',
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)

        response = client.get(f"/assets/{asset.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset.id
        assert data["type"] == "IMAGE"
        assert data["content"] == "https://example.com/specific-image.jpg"
        assert data["campaign_id"] == campaign.id

    def test_get_asset_not_found(self, client: TestClient):
        """Test getting non-existent asset returns 404."""
        response = client.get("/assets/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_asset_various_types(self, client: TestClient, session: Session):
        """Test getting assets of different types."""
        # Create user and campaign
        user = User(
            email="asset_types@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Asset Types Campaign",
            product_url="https://example.com/types",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Test COPY asset
        copy_asset = Asset(
            campaign_id=campaign.id,
            type=AssetType.COPY,
            content="Test ad copy content",
        )
        session.add(copy_asset)
        session.commit()
        session.refresh(copy_asset)

        response = client.get(f"/assets/{copy_asset.id}")
        assert response.status_code == 200
        assert response.json()["type"] == "COPY"

        # Test VIDEO asset
        video_asset = Asset(
            campaign_id=campaign.id,
            type=AssetType.VIDEO,
            content="https://example.com/video.mp4",
        )
        session.add(video_asset)
        session.commit()
        session.refresh(video_asset)

        response = client.get(f"/assets/{video_asset.id}")
        assert response.status_code == 200
        assert response.json()["type"] == "VIDEO"
