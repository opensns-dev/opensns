from typing import Type
from pydantic import BaseModel
from app.core.interfaces import BaseLLMAdapter


class FallbackLLMAdapter(BaseLLMAdapter):
    async def generate_text(self, prompt: str) -> str:
        return f"[Fallback response - configure API key for real generation] {prompt[:50]}..."

    async def generate_structured(
        self, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        data = {field: "fallback_value" for field in schema.__fields__}
        return schema(**data)
