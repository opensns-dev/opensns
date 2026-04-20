from typing import Dict, TypeVar, Generic, Callable, Any
from app.core.interfaces import BaseLLMAdapter, BaseImageAdapter
from app.core.exceptions import EngineNotFoundError
from app.services.audio.interfaces import BaseTTSAdapter, BaseMusicAdapter, BaseSTTAdapter


T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self, engine_type: str):
        self._engines: Dict[str, Callable[[], T]] = {}
        self._engine_type = engine_type

    def register(self, name: str, factory: Callable[[], T]):
        self._engines[name] = factory

    def get(self, name: str) -> T:
        if name not in self._engines:
            raise EngineNotFoundError(
                self._engine_type, name, list(self._engines.keys())
            )
        return self._engines[name]()

    def get_or_none(self, name: str) -> T | None:
        if name not in self._engines:
            return None
        return self._engines[name]()

    def list_engines(self) -> list[str]:
        return list(self._engines.keys())


class EngineRegistry:
    def __init__(self):
        self.llm_registry = Registry[BaseLLMAdapter]("LLM")
        self.image_registry = Registry[BaseImageAdapter]("Image")
        self.video_registry: Registry[Any] = Registry("Video")
        self.tts_registry: Registry[BaseTTSAdapter] = Registry("TTS")
        self.stt_registry: Registry[BaseSTTAdapter] = Registry("STT")
        self.bgm_registry: Registry[BaseMusicAdapter] = Registry("BGM")

    def register_llm_engine(self, name: str, factory: Callable[[], BaseLLMAdapter]):
        self.llm_registry.register(name, factory)

    def get_llm_engine(self, name: str) -> BaseLLMAdapter:
        return self.llm_registry.get(name)

    def register_image_engine(self, name: str, factory: Callable[[], BaseImageAdapter]):
        self.image_registry.register(name, factory)

    def get_image_engine(self, name: str) -> BaseImageAdapter:
        return self.image_registry.get(name)

    def register_video_engine(self, name: str, factory: Callable[[], Any]):
        self.video_registry.register(name, factory)

    def get_video_engine(self, name: str) -> Any:
        return self.video_registry.get(name)

    def get_video_engine_or_none(self, name: str) -> Any:
        return self.video_registry.get_or_none(name)

    def register_tts_engine(self, name: str, factory: Callable[[], BaseTTSAdapter]):
        self.tts_registry.register(name, factory)

    def get_tts_engine(self, name: str) -> BaseTTSAdapter:
        return self.tts_registry.get(name)

    def get_tts_engine_or_none(self, name: str) -> BaseTTSAdapter | None:
        return self.tts_registry.get_or_none(name)

    def register_stt_engine(self, name: str, factory: Callable[[], BaseSTTAdapter]):
        self.stt_registry.register(name, factory)

    def get_stt_engine(self, name: str) -> BaseSTTAdapter:
        return self.stt_registry.get(name)

    def get_stt_engine_or_none(self, name: str) -> BaseSTTAdapter | None:
        return self.stt_registry.get_or_none(name)

    def register_bgm_engine(self, name: str, factory: Callable[[], BaseMusicAdapter]):
        self.bgm_registry.register(name, factory)

    def get_bgm_engine(self, name: str) -> BaseMusicAdapter:
        return self.bgm_registry.get(name)

    def get_bgm_engine_or_none(self, name: str) -> BaseMusicAdapter | None:
        return self.bgm_registry.get_or_none(name)


engine_registry = EngineRegistry()
