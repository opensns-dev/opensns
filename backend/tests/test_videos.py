"""
Tests for videos endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from unittest.mock import patch, MagicMock

from app.models.models import Asset, AssetType, Campaign


class TestListVideos:
    """Tests for GET /videos/campaign/{campaign_id}"""

    def test_list_videos_empty(self, client: TestClient, session: Session):
        """Test listing videos for campaign with no videos."""
        # Create a campaign first
        from app.core.auth import get_password_hash
        from app.models.models import User

        user = User(
            email="video_test@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Video Test Campaign",
            product_url="https://example.com/product",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        response = client.get(f"/videos/campaign/{campaign.id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_videos_with_data(self, client: TestClient, session: Session):
        """Test listing videos returns video assets for campaign."""
        from app.core.auth import get_password_hash
        from app.models.models import User

        user = User(
            email="video_test2@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        campaign = Campaign(
            title="Video Test Campaign 2",
            product_url="https://example.com/product2",
            user_id=user.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Create video assets
        video1 = Asset(
            campaign_id=campaign.id,
            type=AssetType.VIDEO,
            content="https://example.com/video1.mp4",
            asset_metadata='{"duration": 30}',
        )
        video2 = Asset(
            campaign_id=campaign.id,
            type=AssetType.VIDEO,
            content="https://example.com/video2.mp4",
            asset_metadata='{"duration": 60}',
        )
        # Create a non-video asset (should not be returned)
        image = Asset(
            campaign_id=campaign.id,
            type=AssetType.IMAGE,
            content="https://example.com/image.jpg",
        )
        session.add(video1)
        session.add(video2)
        session.add(image)
        session.commit()

        response = client.get(f"/videos/campaign/{campaign.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        contents = [v["content"] for v in data]
        assert "https://example.com/video1.mp4" in contents
        assert "https://example.com/video2.mp4" in contents


class TestGenerateVideo:
    """Tests for POST /videos/generate"""

    @patch("app.api.videos.engine_registry.get_video_engine_or_none")
    def test_generate_video_success(self, mock_get_engine, client: TestClient):
        """Test successful video generation request."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        response = client.post(
            "/videos/generate",
            json={
                "image_url": "https://example.com/image.jpg",
                "motion_prompt": "Camera zoom in slowly",
                "duration": 5.0,
                "engine": "runway",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data
        assert data["video_url"] is None
        mock_get_engine.assert_called_once_with("runway")

    @patch("app.api.videos.engine_registry.get_video_engine_or_none")
    def test_generate_video_invalid_engine(self, mock_get_engine, client: TestClient):
        """Test video generation with invalid engine."""
        mock_get_engine.return_value = None

        with patch(
            "app.api.videos.engine_registry.video_registry.list_engines"
        ) as mock_list:
            mock_list.return_value = ["runway", "kling"]
            response = client.post(
                "/videos/generate",
                json={
                    "image_url": "https://example.com/image.jpg",
                    "engine": "invalid_engine",
                },
            )
            assert response.status_code == 400
            assert "invalid_engine" in response.json()["detail"]

    def test_generate_video_missing_image_url(self, client: TestClient):
        """Test video generation without image_url fails."""
        response = client.post(
            "/videos/generate",
            json={"engine": "runway"},
        )
        assert response.status_code == 422


class TestGetVideoStatus:
    """Tests for GET /videos/status/{task_id}"""

    def test_get_video_status(self, client: TestClient):
        """Test getting video generation status."""
        task_id = "test-task-123"
        response = client.get(f"/videos/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        assert data["video_url"] is None


class TestListEngines:
    """Tests for GET /videos/engines"""

    @patch("app.api.videos.engine_registry.video_registry.list_engines")
    def test_list_engines(self, mock_list_engines, client: TestClient):
        """Test listing available video engines."""
        mock_list_engines.return_value = ["runway", "kling", "cogvideox"]

        response = client.get("/videos/engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert "runway" in data["engines"]
        assert "kling" in data["engines"]
