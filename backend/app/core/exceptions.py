class OpenSNSError(Exception):
    pass


class EngineNotFoundError(OpenSNSError):
    def __init__(self, engine_type: str, name: str, available: list[str]):
        self.engine_type = engine_type
        self.name = name
        self.available = available
        super().__init__(
            f"{engine_type} engine '{name}' not found. Available: {available}"
        )


class APIKeyNotConfiguredError(OpenSNSError):
    def __init__(self, service: str):
        self.service = service
        super().__init__(f"{service} API key is not configured")


class GenerationError(OpenSNSError):
    pass


class ImageGenerationError(GenerationError):
    pass


class VideoGenerationError(GenerationError):
    pass


class WorkflowError(OpenSNSError):
    pass


class ResearchError(OpenSNSError):
    pass
