import json
from typing import Type

from pydantic import BaseModel
import httpx

from app.core.interfaces import BaseLLMAdapter
from app.core.exceptions import APIKeyNotConfiguredError
from app.core.config import settings


class GroqAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model

    async def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Groq")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
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
            raise APIKeyNotConfiguredError("Groq")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
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
            parsed = json.loads(content)
            return schema.model_validate(parsed)
