---
title: Engine System
description: Pluggable AI engine architecture
---

OpenSNS uses a registry-based engine system for flexible AI backend configuration.

## Engine Types

| Type | Purpose | Implementations |
|------|---------|----------------|
| LLM | Text generation | OpenAI, Ollama, Fallback |
| Image | Image generation | Fal.ai, OpenRouter, OpenAI, Replicate, Together, Stability, BFL, Leonardo, Ideogram, ComfyUI |
| Video | Video generation | Fal.ai, Runway, ComfyUI |

## Engine Registry

Central registry for all AI engines:

```python
from app.core.registry import engine_registry

# Register engines at startup
engine_registry.register_llm_engine("openai", lambda: OpenAIAdapter())
engine_registry.register_llm_engine("ollama", lambda: OllamaAdapter())
engine_registry.register_llm_engine("fallback", lambda: FallbackLLMAdapter())

# Get engine by name
llm = engine_registry.get_llm_engine("openai")
```

## LLM Adapters

### Interface

```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        pass
```

### OpenAI Adapter

Uses GPT-4 for high-quality generation:

```python
class OpenAIAdapter(BaseLLMAdapter):
    async def generate(self, prompt, system_prompt=None, temperature=0.7):
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
```

### Ollama Adapter

For local/free LLM usage:

```python
class OllamaAdapter(BaseLLMAdapter):
    async def generate(self, prompt, system_prompt=None, temperature=0.7):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={"model": "llama2", "prompt": prompt}
            )
            return response.json()["response"]
```

### Fallback Adapter

Returns placeholder content when no API keys configured:

```python
class FallbackLLMAdapter(BaseLLMAdapter):
    async def generate(self, prompt, **kwargs):
        return "[Fallback response - configure API keys for real generation]"
```

## Image Adapters

### Interface

```python
class BaseImageAdapter(ABC):
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
    ) -> GenerationResult:
        pass
```

### Fal.ai Adapter

Fast cloud-based image generation:

```python
class FalImageAdapter(BaseImageAdapter):
    async def generate_image(self, prompt, width=1024, height=1024):
        result = await fal.run(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": {"width": width, "height": height}
            }
        )
        return GenerationResult(url=result["images"][0]["url"])
```

## Video Adapters

### Interface

```python
class BaseVideoAdapter(ABC):
    @abstractmethod
    async def image_to_video(
        self,
        image_url: str,
        motion_prompt: str,
        duration: float = 5.0,
    ) -> VideoGenerationResult:
        pass
```

### Fal.ai Video

Converts static images to video:

```python
class FalVideoAdapter(BaseVideoAdapter):
    async def image_to_video(self, image_url, motion_prompt, duration=5.0):
        result = await fal.run(
            "fal-ai/fast-svd-lcm",
            arguments={
                "image_url": image_url,
                "motion_bucket_id": 127
            }
        )
        return VideoGenerationResult(video_url=result["video"]["url"])
```

## Adding Custom Engines

1. **Create adapter class**

```python
class MyCustomAdapter(BaseLLMAdapter):
    async def generate(self, prompt, **kwargs):
        # Your implementation
        pass
```

2. **Register in initializers.py**

```python
engine_registry.register_llm_engine(
    "my-custom",
    lambda: MyCustomAdapter()
)
```

3. **Configure as default**

```bash
DEFAULT_LLM_ENGINE=my-custom
```

## Engine Selection Priority

1. User settings (per-user configuration)
2. Environment variable default
3. Fallback engine
