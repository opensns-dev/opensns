import json
from typing import Type

from pydantic import BaseModel
import httpx

from app.core.interfaces import BaseLLMAdapter
from app.core.exceptions import APIKeyNotConfiguredError
from app.core.config import settings


class GeminiAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Gemini")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_structured(
        self, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Gemini")

        structured_prompt = (
            f"Respond only in valid JSON matching this schema: "
            f"{json.dumps(schema.model_json_schema())}\n\n{prompt}"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": structured_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "responseMimeType": "application/json",
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            return schema.model_validate(parsed)
