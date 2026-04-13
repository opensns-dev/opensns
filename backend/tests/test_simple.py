"""Simple test for ComfyUI adapter."""

import pytest
import asyncio
from app.services.image.comfyui_adapter import ComfyUIAdapter
from app.core.interfaces import AdCreative
from app.services.comfyui_portability import ComfyUICompatibilityError
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_missing_node_error():
    """Test clear error when required node is missing."""
    adapter = ComfyUIAdapter(base_url="http://localhost:8188")
    adapter.discovery.fetch_object_info = AsyncMock(
        return_value={"LoadImageBase64": {}}
    )
    adapter.alias_resolver._available_cache = {"LoadImage", "SaveImage"}

    creative = AdCreative(
        title="Test Ad",
        body="Test body",
        platform="instagram",
    )

    with pytest.raises(ComfyUICompatibilityError) as exc_info:
        await adapter.generate_ad_image(b"fake_image", creative)

    error_msg = str(exc_info.value).lower()
    assert "missing" in error_msg or "node" in error_msg
