"""Mubert music adapter."""

import logging
from typing import List

import httpx

from app.services.audio.interfaces import BaseMusicAdapter, MusicRequest, MusicResult

logger = logging.getLogger(__name__)


class MubertAdapter(BaseMusicAdapter):
    def __init__(self, access_token: str | None = None, customer_id: str | None = None):
        self._access_token = access_token
        self._customer_id = customer_id

    async def generate_music(self, request: MusicRequest) -> MusicResult:
        if not self._access_token:
            logger.warning("Mubert access token not configured")
            return MusicResult()

        try:
            prompt = request.prompt or request.style or "ambient background music"
            payload = {
                "customer-id": self._customer_id,
                "access-token": self._access_token,
                "method": "GetTracksByTags",
                "params": {
                    "tags": [prompt],
                    "duration": int(request.duration),
                    "format": "mp3",
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://music-api.mubert.com/api/v3/public/tracks",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                download_link = data["data"]["tasks"][0]["download_link"]

                audio_response = await client.get(download_link)
                audio_response.raise_for_status()
                audio_data = audio_response.content

            return MusicResult(
                audio_data=audio_data,
                metadata={
                    "engine": "mubert",
                    "prompt": prompt,
                    "duration": request.duration,
                    "download_link": download_link,
                },
            )
        except Exception as e:
            logger.warning("Mubert generation failed: %s", e)
            return MusicResult()

    async def list_styles(self) -> List[str]:
        return ["upbeat", "calm", "corporate", "motivational", "electronic", "ambient"]
