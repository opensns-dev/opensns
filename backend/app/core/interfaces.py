from abc import ABC, abstractmethod
from typing import Any, Type, Dict
from pydantic import BaseModel


class AdCreative(BaseModel):
    title: str
    body: str
    platform: str
    image_prompt: str | None = None


class GenerationResult(BaseModel):
    image_url: str | None = None
    image_data: bytes | None = None
    metadata: Dict[str, Any] = {}


class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> Any:
        pass


class BaseImageAdapter(ABC):
    @abstractmethod
    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        pass


class BaseProductPhotoAdapter(ABC):
    @abstractmethod
    async def remove_background(self, image_data: bytes) -> bytes:
        pass

    @abstractmethod
    async def generate_product_shot(
        self, product_image: bytes, scene_prompt: str, angle: str
    ) -> GenerationResult:
        pass
