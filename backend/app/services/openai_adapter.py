from typing import Type
from pydantic import BaseModel
from app.core.interfaces import BaseLLMAdapter
from app.core.exceptions import APIKeyNotConfiguredError
from app.core.config import settings
import httpx


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = base_url or settings.OPENAI_BASE_URL

    async def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise APIKeyNotConfiguredError("OpenAI")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_structured(
        self, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        if not self.api_key:
            raise APIKeyNotConfiguredError("OpenAI")

        schema.model_json_schema()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            import json

            parsed = json.loads(content)
            return schema.model_validate(parsed)
