"""
Tests for repurpose endpoints.
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from unittest.mock import patch

from app.models.models import (
    RepurposeJob,
    RepurposeContent,
    ContentPlatform,
    RepurposeStatus,
    ToneStyle,
    User,
)


class TestListRepurposeJobs:
    """Tests for GET /repurpose"""

    def test_list_empty(self, client: TestClient, auth_headers: dict):
        """Test listing repurpose jobs when user has none."""
        response = client.get("/repurpose/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test listing repurpose jobs returns user's jobs."""
        job1 = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://www.youtube.com/watch?v=abc123",
            target_platforms=json.dumps(["instagram", "blog"]),
            status=RepurposeStatus.PENDING,
        )
        job2 = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://youtu.be/def456",
            target_platforms=json.dumps(["twitter"]),
            status=RepurposeStatus.COMPLETED,
        )
        session.add(job1)
        session.add(job2)
        session.commit()

        response = client.get("/repurpose/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        urls = [j["youtube_url"] for j in data]
        assert "https://www.youtube.com/watch?v=abc123" in urls
        assert "https://youtu.be/def456" in urls

    def test_list_only_own(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test that users only see their own repurpose jobs."""
        from app.core.auth import get_password_hash

        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        other_job = RepurposeJob(
            user_id=other_user.id,
            youtube_url="https://www.youtube.com/watch?v=other123",
            target_platforms=json.dumps(["blog"]),
        )
        session.add(other_job)
        session.commit()

        response = client.get("/repurpose/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_unauthenticated(self, client: TestClient):
        """Test listing repurpose jobs without auth fails."""
        response = client.get("/repurpose/")
        assert response.status_code == 401


class TestCreateRepurposeJob:
    """Tests for POST /repurpose/"""

    @patch("app.api.repurpose.run_repurpose_pipeline")
    @patch("app.api.repurpose.check_credits")
    def test_create_success(
        self, mock_check_credits, mock_pipeline, client: TestClient, auth_headers: dict
    ):
        """Test successful repurpose job creation."""
        response = client.post(
            "/repurpose/",
            headers=auth_headers,
            json={
                "youtube_url": "https://www.youtube.com/watch?v=test123",
                "target_platforms": ["INSTAGRAM", "NAVER_BLOG"],
                "tone_style": "FRIENDLY",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["youtube_url"] == "https://www.youtube.com/watch?v=test123"
        assert data["status"] == "PENDING"
        assert "INSTAGRAM" in data["target_platforms"]
        assert "NAVER_BLOG" in data["target_platforms"]
        assert "id" in data
        mock_check_credits.assert_called_once()
        mock_pipeline.assert_called_once()

    @patch("app.api.repurpose.run_repurpose_pipeline")
    @patch("app.api.repurpose.check_credits")
    def test_create_with_defaults(
        self, mock_check_credits, mock_pipeline, client: TestClient, auth_headers: dict
    ):
        """Test repurpose job creation with default tone_style."""
        response = client.post(
            "/repurpose/",
            headers=auth_headers,
            json={
                "youtube_url": "https://youtu.be/shorturl",
                "target_platforms": ["INSTAGRAM"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["youtube_url"] == "https://youtu.be/shorturl"
        assert data["tone_style"] == "FRIENDLY"

    def test_create_invalid_url(self, client: TestClient, auth_headers: dict):
        """Test creating repurpose job with invalid YouTube URL fails."""
        response = client.post(
            "/repurpose/",
            headers=auth_headers,
            json={
                "youtube_url": "https://example.com/not-youtube",
                "target_platforms": ["INSTAGRAM"],
            },
        )
        assert response.status_code == 400
        assert (
            "youtube" in response.json()["detail"].lower()
            or "유효한" in response.json()["detail"]
        )

    def test_create_missing_url(self, client: TestClient, auth_headers: dict):
        """Test creating repurpose job without URL fails."""
        response = client.post(
            "/repurpose/",
            headers=auth_headers,
            json={"target_platforms": ["instagram"]},
        )
        assert response.status_code == 422

    def test_create_unauthenticated(self, client: TestClient):
        """Test creating repurpose job without auth fails."""
        response = client.post(
            "/repurpose/",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=test123",
                "target_platforms": ["instagram"],
            },
        )
        assert response.status_code == 401


class TestGetRepurposeJob:
    """Tests for GET /repurpose/{job_id}"""

    def test_get_job_success(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test getting a specific repurpose job."""
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://www.youtube.com/watch?v=specific123",
            target_platforms=json.dumps(["instagram", "blog"]),
            status=RepurposeStatus.COMPLETED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/repurpose/{job.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["youtube_url"] == "https://www.youtube.com/watch?v=specific123"
        assert data["status"] == "COMPLETED"

    def test_get_job_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent repurpose job returns 404."""
        response = client.get("/repurpose/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_job_other_user(
        self, client: TestClient, session: Session, auth_headers: dict
    ):
        """Test getting another user's repurpose job returns 404."""
        from app.core.auth import get_password_hash

        other_user = User(
            email="other2@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        other_job = RepurposeJob(
            user_id=other_user.id,
            youtube_url="https://www.youtube.com/watch?v=private123",
            target_platforms=json.dumps(["blog"]),
        )
        session.add(other_job)
        session.commit()
        session.refresh(other_job)

        response = client.get(f"/repurpose/{other_job.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_job_unauthenticated(self, client: TestClient):
        """Test getting repurpose job without auth fails."""
        response = client.get("/repurpose/1")
        assert response.status_code == 401


class TestGetRepurposeContents:
    """Tests for GET /repurpose/{job_id}/contents"""

    def test_get_contents_success(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test getting contents for a repurpose job."""
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://www.youtube.com/watch?v=content123",
            target_platforms=json.dumps(["instagram", "blog"]),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        content1 = RepurposeContent(
            job_id=job.id,
            platform=ContentPlatform.INSTAGRAM,
            content="Instagram post content",
            content_metadata=json.dumps({"hashtags": ["#test"]}),
        )
        content2 = RepurposeContent(
            job_id=job.id,
            platform=ContentPlatform.NAVER_BLOG,
            content="Blog post content",
            content_metadata=json.dumps({"word_count": 500}),
        )
        session.add(content1)
        session.add(content2)
        session.commit()

        response = client.get(f"/repurpose/{job.id}/contents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        platforms = [c["platform"] for c in data]
        assert "INSTAGRAM" in platforms
        assert "NAVER_BLOG" in platforms

    def test_get_contents_empty(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test getting contents for job with no contents."""
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://www.youtube.com/watch?v=empty123",
            target_platforms=json.dumps(["instagram"]),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/repurpose/{job.id}/contents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_contents_job_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting contents for non-existent job returns 404."""
        response = client.get("/repurpose/99999/contents", headers=auth_headers)
        assert response.status_code == 404

    def test_get_contents_unauthenticated(self, client: TestClient):
        """Test getting contents without auth fails."""
        response = client.get("/repurpose/1/contents")
        assert response.status_code == 401


class TestDeleteRepurposeJob:
    """Tests for DELETE /repurpose/{job_id}"""

    def test_delete_job_success(
        self, client: TestClient, session: Session, test_user: User, auth_headers: dict
    ):
        """Test deleting a repurpose job."""
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://www.youtube.com/watch?v=delete123",
            target_platforms=json.dumps(["instagram"]),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.delete(f"/repurpose/{job.id}", headers=auth_headers)
        assert response.status_code == 200
        assert (
            "삭제" in response.json()["message"]
            or "deleted" in response.json()["message"].lower()
        )

        # Verify job is deleted
        response = client.get(f"/repurpose/{job.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_job_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent repurpose job returns 404."""
        response = client.delete("/repurpose/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_job_other_user(
        self, client: TestClient, session: Session, auth_headers: dict
    ):
        """Test deleting another user's repurpose job returns 404."""
        from app.core.auth import get_password_hash

        other_user = User(
            email="other3@example.com",
            hashed_password=get_password_hash("password"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        other_job = RepurposeJob(
            user_id=other_user.id,
            youtube_url="https://www.youtube.com/watch?v=otherdelete123",
            target_platforms=json.dumps(["blog"]),
        )
        session.add(other_job)
        session.commit()
        session.refresh(other_job)

        response = client.delete(f"/repurpose/{other_job.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_job_unauthenticated(self, client: TestClient):
        """Test deleting repurpose job without auth fails."""
        response = client.delete("/repurpose/1")
        assert response.status_code == 401
