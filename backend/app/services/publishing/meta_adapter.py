import logging
from urllib.parse import urlencode

from app.core.config import settings
from app.core.http_client import get_http_client

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

OAUTH_SCOPES = [
    "pages_manage_posts",
    "pages_read_engagement",
    "instagram_basic",
    "instagram_content_publish",
]


class MetaPublishingAdapter:
    def get_oauth_url(self, state: str) -> str:
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "scope": ",".join(OAUTH_SCOPES),
            "response_type": "code",
            "state": state,
        }
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        client = await get_http_client()
        token_resp = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
                "code": code,
            },
        )
        token_data = token_resp.json()
        if "error" in token_data:
            logger.error("Meta token exchange failed: %s", token_data["error"])
            raise ValueError(
                token_data["error"].get("message", "Token exchange failed")
            )

        short_token = token_data["access_token"]

        ll_resp = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "fb_exchange_token": short_token,
            },
        )
        ll_data = ll_resp.json()
        if "error" in ll_data:
            logger.error("Meta long-lived token exchange failed: %s", ll_data["error"])
            raise ValueError(
                ll_data["error"].get("message", "Long-lived token exchange failed")
            )

        return {
            "access_token": ll_data["access_token"],
            "expires_in": ll_data.get("expires_in"),
        }

    async def get_user_info(self, access_token: str) -> dict:
        client = await get_http_client()
        resp = await client.get(
            f"{GRAPH_API_BASE}/me",
            params={"access_token": access_token, "fields": "id,name"},
        )
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"].get("message", "Failed to get user info"))
        return data

    async def get_pages(self, access_token: str) -> list[dict]:
        client = await get_http_client()
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,access_token,instagram_business_account",
            },
        )
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"].get("message", "Failed to get pages"))
        return data.get("data", [])

    async def publish_to_facebook(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        image_url: str | None = None,
    ) -> dict:
        client = await get_http_client()
        try:
            if image_url:
                resp = await client.post(
                    f"{GRAPH_API_BASE}/{page_id}/photos",
                    params={"access_token": page_access_token},
                    data={"message": message, "url": image_url},
                )
            else:
                resp = await client.post(
                    f"{GRAPH_API_BASE}/{page_id}/feed",
                    params={"access_token": page_access_token},
                    data={"message": message},
                )
            data = resp.json()
            if "error" in data:
                return {
                    "success": False,
                    "error": data["error"].get("message", "Publish failed"),
                }
            return {
                "success": True,
                "post_id": data.get("id") or data.get("post_id"),
                "post_url": f"https://www.facebook.com/{data.get('id', '')}",
            }
        except Exception as e:
            logger.exception("Facebook publish error")
            return {"success": False, "error": str(e)}

    async def publish_to_instagram(
        self,
        page_access_token: str,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> dict:
        client = await get_http_client()
        try:
            container_resp = await client.post(
                f"{GRAPH_API_BASE}/{ig_user_id}/media",
                params={"access_token": page_access_token},
                data={"image_url": image_url, "caption": caption},
            )
            container_data = container_resp.json()
            if "error" in container_data:
                return {
                    "success": False,
                    "error": container_data["error"].get(
                        "message", "Container creation failed"
                    ),
                }

            creation_id = container_data["id"]

            publish_resp = await client.post(
                f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
                params={"access_token": page_access_token},
                data={"creation_id": creation_id},
            )
            publish_data = publish_resp.json()
            if "error" in publish_data:
                return {
                    "success": False,
                    "error": publish_data["error"].get("message", "Publish failed"),
                }
            return {
                "success": True,
                "post_id": publish_data.get("id"),
                "post_url": f"https://www.instagram.com/p/{publish_data.get('id', '')}",
            }
        except Exception as e:
            logger.exception("Instagram publish error")
            return {"success": False, "error": str(e)}
