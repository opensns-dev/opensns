import base64
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.publishing.threads_adapter import ThreadsPublishingAdapter
from app.services.publishing.x_adapter import XPublishingAdapter


def _mock_response(json_data: dict, status_code: int = 200) -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.text = ""
    return resp


class TestXPublishingAdapter:
    def setup_method(self):
        self.adapter = XPublishingAdapter()

    @patch("app.services.publishing.x_adapter.settings")
    def test_get_oauth_url_returns_pkce_params(self, mock_settings):
        mock_settings.TWITTER_CLIENT_ID = "test_client_id"
        mock_settings.TWITTER_REDIRECT_URI = (
            "http://localhost:8000/publishing/x/callback"
        )

        auth_url, code_verifier = self.adapter.get_oauth_url("test_state")

        assert "x.com/i/oauth2/authorize" in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert "state=test_state" in auth_url
        assert "tweet.read" in auth_url
        assert "tweet.write" in auth_url
        assert "offline.access" in auth_url

        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        expected_challenge = (
            base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        )
        assert expected_challenge in auth_url

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    @patch("app.services.publishing.x_adapter.settings")
    async def test_exchange_code_success(self, mock_settings, mock_get_client):
        mock_settings.TWITTER_CLIENT_ID = "test_id"
        mock_settings.TWITTER_CLIENT_SECRET = "test_secret"
        mock_settings.TWITTER_REDIRECT_URI = "http://localhost/callback"

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "access_token": "access_123",
                "refresh_token": "refresh_456",
                "expires_in": 7200,
            }
        )

        result = await self.adapter.exchange_code("auth_code_abc", "verifier_xyz")

        assert result["access_token"] == "access_123"
        assert result["refresh_token"] == "refresh_456"
        assert result["expires_in"] == 7200

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["data"]["grant_type"] == "authorization_code"
        assert call_kwargs.kwargs["data"]["code"] == "auth_code_abc"
        assert call_kwargs.kwargs["data"]["code_verifier"] == "verifier_xyz"

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    @patch("app.services.publishing.x_adapter.settings")
    async def test_exchange_code_error(self, mock_settings, mock_get_client):
        mock_settings.TWITTER_CLIENT_ID = "test_id"
        mock_settings.TWITTER_CLIENT_SECRET = "test_secret"
        mock_settings.TWITTER_REDIRECT_URI = "http://localhost/callback"

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "error": "invalid_grant",
                "error_description": "Code expired",
            }
        )

        with pytest.raises(ValueError, match="Code expired"):
            await self.adapter.exchange_code("bad_code", "verifier")

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    async def test_get_user_info(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = _mock_response(
            {
                "data": {"id": "12345", "name": "Test User", "username": "testuser"},
            }
        )

        result = await self.adapter.get_user_info("token_abc")

        assert result["id"] == "12345"
        assert result["name"] == "Test User"
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    async def test_publish_tweet_text_only(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "data": {"id": "tweet_999"},
            }
        )

        result = await self.adapter.publish_tweet("token_abc", "Hello world!")

        assert result["success"] is True
        assert result["post_id"] == "tweet_999"
        assert "x.com/i/status/tweet_999" in result["post_url"]

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["json"] == {"text": "Hello world!"}

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    async def test_publish_tweet_with_media(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "data": {"id": "tweet_888"},
            }
        )

        result = await self.adapter.publish_tweet(
            "token_abc", "Check this out!", media_id="media_777"
        )

        assert result["success"] is True
        assert result["post_id"] == "tweet_888"

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["text"] == "Check this out!"
        assert payload["media"] == {"media_ids": ["media_777"]}

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    async def test_publish_tweet_api_error(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "errors": [{"message": "Rate limit exceeded"}],
            }
        )

        result = await self.adapter.publish_tweet("token_abc", "test")

        assert result["success"] is False
        assert "Rate limit exceeded" in result["error"]

    @pytest.mark.asyncio
    @patch("app.services.publishing.x_adapter.get_http_client")
    @patch("app.services.publishing.x_adapter.settings")
    async def test_refresh_token(self, mock_settings, mock_get_client):
        mock_settings.TWITTER_CLIENT_ID = "test_id"
        mock_settings.TWITTER_CLIENT_SECRET = "test_secret"

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "expires_in": 7200,
            }
        )

        result = await self.adapter.refresh_token("old_refresh")

        assert result["access_token"] == "new_access"
        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["data"]["grant_type"] == "refresh_token"


class TestThreadsPublishingAdapter:
    def setup_method(self):
        self.adapter = ThreadsPublishingAdapter()

    @patch("app.services.publishing.threads_adapter.settings")
    def test_get_oauth_url_correct_scopes(self, mock_settings):
        mock_settings.THREADS_APP_ID = "threads_app_123"
        mock_settings.THREADS_REDIRECT_URI = (
            "http://localhost:8000/publishing/threads/callback"
        )

        url = self.adapter.get_oauth_url("state_abc")

        assert "threads.net/oauth/authorize" in url
        assert "client_id=threads_app_123" in url
        assert "threads_basic" in url
        assert "threads_content_publish" in url
        assert "state=state_abc" in url
        assert "response_type=code" in url

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    @patch("app.services.publishing.threads_adapter.settings")
    async def test_exchange_code_and_long_lived_token(
        self, mock_settings, mock_get_client
    ):
        mock_settings.THREADS_APP_ID = "app_123"
        mock_settings.THREADS_APP_SECRET = "secret_456"
        mock_settings.THREADS_REDIRECT_URI = "http://localhost/callback"

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_client.post.return_value = _mock_response(
            {
                "access_token": "short_token_xyz",
                "expires_in": 3600,
            }
        )

        short_result = await self.adapter.exchange_code("code_abc")
        assert short_result["access_token"] == "short_token_xyz"

        mock_client.get.return_value = _mock_response(
            {
                "access_token": "long_token_abc",
                "expires_in": 5184000,
            }
        )

        long_result = await self.adapter.exchange_long_lived_token(
            short_result["access_token"]
        )
        assert long_result["access_token"] == "long_token_abc"
        assert long_result["expires_in"] == 5184000

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    @patch("app.services.publishing.threads_adapter.settings")
    async def test_exchange_code_error(self, mock_settings, mock_get_client):
        mock_settings.THREADS_APP_ID = "app_123"
        mock_settings.THREADS_APP_SECRET = "secret_456"
        mock_settings.THREADS_REDIRECT_URI = "http://localhost/callback"

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.post.return_value = _mock_response(
            {
                "error": "invalid_code",
                "error_message": "Code is invalid",
            }
        )

        with pytest.raises(ValueError, match="Code is invalid"):
            await self.adapter.exchange_code("bad_code")

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    async def test_get_user_info(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = _mock_response(
            {
                "id": "user_999",
                "username": "threadsuser",
            }
        )

        result = await self.adapter.get_user_info("token_abc")

        assert result["id"] == "user_999"
        assert result["username"] == "threadsuser"

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    async def test_create_and_publish_container_text(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_client.post.side_effect = [
            _mock_response({"id": "container_111"}),
            _mock_response({"id": "post_222"}),
        ]

        result = await self.adapter.publish_to_threads(
            access_token="token_abc",
            user_id="user_999",
            text="Hello from Threads!",
        )

        assert result["success"] is True
        assert result["post_id"] == "post_222"
        assert "threads.net" in result["post_url"]

        create_call = mock_client.post.call_args_list[0]
        assert "user_999/threads" in str(create_call)
        assert create_call.kwargs["params"]["media_type"] == "TEXT"

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    async def test_create_and_publish_container_with_image(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_client.post.side_effect = [
            _mock_response({"id": "container_333"}),
            _mock_response({"id": "post_444"}),
        ]

        result = await self.adapter.publish_to_threads(
            access_token="token_abc",
            user_id="user_999",
            text="Photo post!",
            image_url="https://example.com/photo.jpg",
        )

        assert result["success"] is True
        assert result["post_id"] == "post_444"

        create_call = mock_client.post.call_args_list[0]
        assert create_call.kwargs["params"]["media_type"] == "IMAGE"
        assert (
            create_call.kwargs["params"]["image_url"] == "https://example.com/photo.jpg"
        )

    @pytest.mark.asyncio
    @patch("app.services.publishing.threads_adapter.get_http_client")
    async def test_publish_to_threads_container_error(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_client.post.return_value = _mock_response(
            {
                "error": {"message": "Invalid user", "code": 100},
            }
        )

        result = await self.adapter.publish_to_threads(
            access_token="token_abc",
            user_id="bad_user",
            text="test",
        )

        assert result["success"] is False
        assert "Invalid user" in result["error"]
