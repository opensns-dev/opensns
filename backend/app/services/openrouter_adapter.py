from typing import Type
from pydantic import BaseModel
from app.core.interfaces import BaseLLMAdapter
from app.core.exceptions import APIKeyNotConfiguredError
from app.core.config import settings
import httpx

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterAdapter(BaseLLMAdapter):
    """OpenRouter LLM adapter — OpenAI-compatible API with model routing.

    OpenRouter provides access to 200+ models (OpenAI, Anthropic, Google, Meta, etc.)
    via a single API key and OpenAI-compatible endpoint.

    Model names use provider prefix: "openai/gpt-4o", "anthropic/claude-sonnet-4",
    "google/gemini-2.5-pro", "meta-llama/llama-3-70b-instruct", etc.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.FRONTEND_URL,
            "X-Title": settings.PROJECT_NAME,
        }

    async def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise APIKeyNotConfiguredError("OpenRouter")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self._headers(),
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
            raise APIKeyNotConfiguredError("OpenRouter")

        schema.model_json_schema()

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self._headers(),
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
