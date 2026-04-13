import logging
from urllib.parse import urlencode

from app.core.config import settings
from app.core.http_client import get_http_client

logger = logging.getLogger(__name__)

THREADS_AUTH_URL = "https://threads.net/oauth/authorize"
THREADS_GRAPH_BASE = "https://graph.threads.net"

OAUTH_SCOPES = ["threads_basic", "threads_content_publish"]


class ThreadsPublishingAdapter:
    def get_oauth_url(self, state: str) -> str:
        params = {
            "client_id": settings.THREADS_APP_ID,
            "redirect_uri": settings.THREADS_REDIRECT_URI,
            "scope": ",".join(OAUTH_SCOPES),
            "response_type": "code",
            "state": state,
        }
        return f"{THREADS_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        client = await get_http_client()
        resp = await client.post(
            f"{THREADS_GRAPH_BASE}/oauth/access_token",
            data={
                "client_id": settings.THREADS_APP_ID,
                "client_secret": settings.THREADS_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.THREADS_REDIRECT_URI,
                "code": code,
            },
        )
        data = resp.json()
        if "error" in data:
            logger.error("Threads token exchange failed: %s", data)
            raise ValueError(data.get("error_message", "Token exchange failed"))
        return {
            "access_token": data["access_token"],
            "expires_in": data.get("expires_in"),
        }

    async def exchange_long_lived_token(self, short_token: str) -> dict:
        client = await get_http_client()
        resp = await client.get(
            f"{THREADS_GRAPH_BASE}/access_token",
            params={
                "grant_type": "th_exchange_token",
                "client_secret": settings.THREADS_APP_SECRET,
                "access_token": short_token,
            },
        )
        data = resp.json()
        if "error" in data:
            logger.error("Threads long-lived token exchange failed: %s", data)
            raise ValueError(
                data.get("error_message", "Long-lived token exchange failed")
            )
        return {
            "access_token": data["access_token"],
            "expires_in": data.get("expires_in"),
        }

    async def get_user_info(self, access_token: str) -> dict:
        client = await get_http_client()
        resp = await client.get(
            f"{THREADS_GRAPH_BASE}/v1.0/me",
            params={
                "fields": "id,username",
                "access_token": access_token,
            },
        )
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"].get("message", "Failed to get user info"))
        return {"id": data.get("id"), "username": data.get("username")}

    async def create_container(
        self,
        access_token: str,
        user_id: str,
        text: str,
        media_type: str = "TEXT",
        image_url: str | None = None,
    ) -> str:
        client = await get_http_client()
        params: dict = {
            "media_type": media_type,
            "text": text,
            "access_token": access_token,
        }
        if image_url and media_type == "IMAGE":
            params["image_url"] = image_url

        resp = await client.post(
            f"{THREADS_GRAPH_BASE}/v1.0/{user_id}/threads",
            params=params,
        )
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"].get("message", "Container creation failed"))
        return data["id"]

    async def publish_container(
        self,
        access_token: str,
        user_id: str,
        creation_id: str,
    ) -> str:
        client = await get_http_client()
        resp = await client.post(
            f"{THREADS_GRAPH_BASE}/v1.0/{user_id}/threads_publish",
            params={
                "creation_id": creation_id,
                "access_token": access_token,
            },
        )
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"].get("message", "Publish failed"))
        return data["id"]

    async def publish_to_threads(
        self,
        access_token: str,
        user_id: str,
        text: str,
        image_url: str | None = None,
    ) -> dict:
        try:
            media_type = "IMAGE" if image_url else "TEXT"
            container_id = await self.create_container(
                access_token=access_token,
                user_id=user_id,
                text=text,
                media_type=media_type,
                image_url=image_url,
            )
            post_id = await self.publish_container(
                access_token=access_token,
                user_id=user_id,
                creation_id=container_id,
            )
            return {
                "success": True,
                "post_id": post_id,
                "post_url": f"https://www.threads.net/post/{post_id}",
            }
        except Exception as e:
            logger.exception("Threads publish error")
            return {"success": False, "error": str(e)}
