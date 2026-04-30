"""Notify the Vaktram API that recording audio is ready.

If R2 is configured, the FLAC is uploaded to Cloudflare R2 first and the API
is told the `r2://...` URI. Otherwise we send the local filesystem path,
which works in docker-compose where bot and API share a volume.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import httpx

from bot.audio import r2_uploader

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000")
DEFAULT_REGION = os.getenv("REGION", "us-east-1")


async def upload_audio_to_api(
    local_path: str,
    meeting_id: str,
    user_id: str,
    organization_id: Optional[str] = None,
) -> str:
    """Persist audio to durable storage (R2 or shared volume) and notify the API."""
    file_path = Path(local_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {local_path}")

    if r2_uploader.is_configured():
        storage_uri = await r2_uploader.upload_flac(
            local_path=local_path,
            region=DEFAULT_REGION,
            organization_id=organization_id,
            meeting_id=meeting_id,
        )
    else:
        # Legacy: rely on a shared volume between bot and API
        storage_uri = str(file_path)
        logger.info(
            "R2 not configured, falling back to local path: %s", storage_uri
        )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_URL}/internal/meetings/{meeting_id}/audio-ready",
            json={"audio_storage_path": storage_uri, "user_id": user_id},
        )
        resp.raise_for_status()

    logger.info(
        "API notified: audio ready for meeting %s (%s, %d bytes)",
        meeting_id, file_path.name, file_path.stat().st_size,
    )
    return storage_uri
