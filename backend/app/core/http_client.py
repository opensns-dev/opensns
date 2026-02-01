import httpx
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class HTTPClientManager:
    _instance: "HTTPClientManager | None" = None
    _client: httpx.AsyncClient | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None


http_client_manager = HTTPClientManager()


async def get_http_client() -> httpx.AsyncClient:
    return await http_client_manager.get_client()


@asynccontextmanager
async def managed_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    client = await get_http_client()
    try:
        yield client
    except Exception:
        raise
