import json
from typing import Type

from pydantic import BaseModel
import httpx

from app.core.interfaces import BaseLLMAdapter
from app.core.exceptions import APIKeyNotConfiguredError
from app.core.config import settings


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model

    async def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Anthropic")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def generate_structured(
        self, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Anthropic")

        system_prompt = (
            f"Respond only in valid JSON matching this schema: "
            f"{json.dumps(schema.model_json_schema())}"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            parsed = json.loads(content)
            return schema.model_validate(parsed)
