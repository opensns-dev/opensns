import asyncio
import base64
import hashlib
import logging
import secrets
from urllib.parse import urlencode

from app.core.config import settings
from app.core.http_client import get_http_client

logger = logging.getLogger(__name__)

X_AUTH_URL = "https://x.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_API_BASE = "https://api.x.com/2"

OAUTH_SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "media.write",
    "offline.access",
]


class XPublishingAdapter:
    def get_oauth_url(self, state: str) -> tuple[str, str]:
        code_verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        params = {
            "response_type": "code",
            "client_id": settings.TWITTER_CLIENT_ID,
            "redirect_uri": settings.TWITTER_REDIRECT_URI,
            "scope": " ".join(OAUTH_SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{X_AUTH_URL}?{urlencode(params)}"
        return auth_url, code_verifier

    async def exchange_code(self, code: str, code_verifier: str) -> dict:
        client = await get_http_client()
        credentials = f"{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}"
        basic_auth = base64.b64encode(credentials.encode()).decode()

        resp = await client.post(
            X_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {basic_auth}",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.TWITTER_REDIRECT_URI,
                "code_verifier": code_verifier,
            },
        )
        data = resp.json()
        if "error" in data:
            logger.error("X token exchange failed: %s", data)
            raise ValueError(data.get("error_description", "Token exchange failed"))

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        client = await get_http_client()
        credentials = f"{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}"
        basic_auth = base64.b64encode(credentials.encode()).decode()

        resp = await client.post(
            X_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {basic_auth}",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        data = resp.json()
        if "error" in data:
            logger.error("X token refresh failed: %s", data)
            raise ValueError(data.get("error_description", "Token refresh failed"))

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
        }

    async def get_user_info(self, access_token: str) -> dict:
        client = await get_http_client()
        resp = await client.get(
            f"{X_API_BASE}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = resp.json()
        if "errors" in data:
            raise ValueError(
                data["errors"][0].get("message", "Failed to get user info")
            )
        user_data = data.get("data", {})
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "username": user_data.get("username"),
        }

    async def upload_media(
        self,
        access_token: str,
        image_data: bytes,
        media_type: str = "image/jpeg",
    ) -> str | None:
        client = await get_http_client()
        headers = {"Authorization": f"Bearer {access_token}"}
        upload_url = f"{X_API_BASE}/media/upload"

        try:
            # INIT
            init_resp = await client.post(
                upload_url,
                headers=headers,
                data={
                    "command": "INIT",
                    "media_type": media_type,
                    "total_bytes": str(len(image_data)),
                    "media_category": "tweet_image",
                },
            )
            init_data = init_resp.json()
            if "error" in init_data or "errors" in init_data:
                logger.error("X media INIT failed: %s", init_data)
                return None
            media_id = init_data.get("media_id_string") or str(
                init_data.get("media_id", "")
            )

            # APPEND
            append_resp = await client.post(
                upload_url,
                headers=headers,
                data={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": "0",
                },
                files={"media": ("media", image_data, media_type)},
            )
            if append_resp.status_code not in (200, 202, 204):
                logger.error(
                    "X media APPEND failed: %s %s",
                    append_resp.status_code,
                    append_resp.text,
                )
                return None

            # FINALIZE
            finalize_resp = await client.post(
                upload_url,
                headers=headers,
                data={"command": "FINALIZE", "media_id": media_id},
            )
            finalize_data = finalize_resp.json()
            if "error" in finalize_data or "errors" in finalize_data:
                logger.error("X media FINALIZE failed: %s", finalize_data)
                return None

            # Poll processing_info if needed
            processing = finalize_data.get("processing_info")
            while processing and processing.get("state") in (
                "pending",
                "in_progress",
            ):
                wait_secs = processing.get("check_after_secs", 2)
                await asyncio.sleep(wait_secs)
                status_resp = await client.get(
                    upload_url,
                    headers=headers,
                    params={"command": "STATUS", "media_id": media_id},
                )
                status_data = status_resp.json()
                processing = status_data.get("processing_info")
                if processing and processing.get("state") == "failed":
                    logger.error("X media processing failed: %s", processing)
                    return None

            return media_id

        except Exception as e:
            logger.exception("X media upload error: %s", e)
            return None

    async def publish_tweet(
        self,
        access_token: str,
        text: str,
        media_id: str | None = None,
    ) -> dict:
        client = await get_http_client()
        try:
            payload: dict = {"text": text}
            if media_id:
                payload["media"] = {"media_ids": [media_id]}

            resp = await client.post(
                f"{X_API_BASE}/tweets",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            data = resp.json()
            if "errors" in data:
                return {
                    "success": False,
                    "error": data["errors"][0].get("message", "Publish failed"),
                }
            tweet_data = data.get("data", {})
            tweet_id = tweet_data.get("id", "")
            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": f"https://x.com/i/status/{tweet_id}",
            }
        except Exception as e:
            logger.exception("X publish error")
            return {"success": False, "error": str(e)}
