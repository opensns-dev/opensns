"""S3-compatible object storage for persistent asset URLs.

Works with Cloudflare R2, AWS S3, and MinIO. Must be configured before running campaigns.
"""

import asyncio
import logging
import os
from functools import lru_cache

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings
from app.core.http_client import get_http_client

logger = logging.getLogger(__name__)


def is_storage_configured() -> bool:
    return bool(
        settings.STORAGE_ENDPOINT_URL
        and settings.STORAGE_ACCESS_KEY_ID
        and settings.STORAGE_SECRET_ACCESS_KEY
        and settings.STORAGE_PUBLIC_URL
    )


@lru_cache(maxsize=1)
def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.STORAGE_ENDPOINT_URL,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY_ID,
        aws_secret_access_key=settings.STORAGE_SECRET_ACCESS_KEY,
        region_name=settings.STORAGE_REGION,
        config=BotoConfig(
            signature_version="s3v4",
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def generate_key(campaign_id: int, asset_type: str, index: int, ext: str) -> str:
    return f"campaigns/{campaign_id}/{asset_type}/{index}.{ext}"


def _is_url(content: str) -> bool:
    return content.startswith("http://") or content.startswith("https://")


def _is_file_path(content: str) -> bool:
    return os.path.exists(content)


def _upload_bytes(data: bytes, key: str, content_type: str) -> None:
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.STORAGE_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def _build_public_url(key: str) -> str:
    base = (settings.STORAGE_PUBLIC_URL or "").rstrip("/")
    return f"{base}/{key}"


async def upload_asset(content: bytes | str, key: str, content_type: str) -> str:
    """Upload bytes, a URL, or a local file path to S3. Returns the public URL."""
    data: bytes

    if isinstance(content, bytes):
        data = content
    elif isinstance(content, str) and _is_url(content):
        client = await get_http_client()
        resp = await client.get(content)
        resp.raise_for_status()
        data = resp.content
    elif isinstance(content, str) and _is_file_path(content):
        data = await asyncio.to_thread(_read_file, content)
    else:
        raise ValueError(f"Cannot resolve content to uploadable data: {content[:80]}")

    await asyncio.to_thread(_upload_bytes, data, key, content_type)

    return _build_public_url(key)


def _read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()
