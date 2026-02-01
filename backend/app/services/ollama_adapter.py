from typing import Type
from pydantic import BaseModel
from app.core.interfaces import BaseLLMAdapter
import httpx


class OllamaAdapter(BaseLLMAdapter):
    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.1"
    ):
        self.base_url = base_url
        self.model = model

    async def generate_text(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json().get("response", "")

    async def generate_structured(
        self, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        # Simple implementation using system prompt for JSON
        system_prompt = (
            f"Respond only in valid JSON matching this schema: {schema.schema_json()}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\nUser: {prompt}",
                    "stream": False,
                    "format": "json",
                },
                timeout=60.0,
            )
            response.raise_for_status()
            text = response.json().get("response", "")
            return schema.parse_raw(text)
