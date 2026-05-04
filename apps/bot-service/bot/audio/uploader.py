"""Persist audio FLAC to durable storage and notify the API.

Picks the first configured backend in this order:
  1. Supabase Storage  (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)  ← production
  2. Cloudflare R2     (R2_ACCOUNT_ID + R2_ACCESS_KEY_ID + R2_SECRET_ACCESS_KEY)
  3. Local filesystem path  (only useful when bot and API share a volume,
                             i.e. docker-compose on a single host)

The API stores whichever URI is returned in `meeting.audio_url`; the
transcription pipeline uses `r2_storage_service.fetch_bytes(uri)` which
understands `supabase://`, `r2://`, `s3://`, and bare local paths.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import httpx

from bot.audio import r2_uploader, supabase_uploader

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000")
DEFAULT_REGION = os.getenv("REGION", "us-east-1")


async def upload_audio_to_api(
    local_path: str,
    meeting_id: str,
    user_id: str,
    organization_id: Optional[str] = None,
) -> str:
    file_path = Path(local_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {local_path}")

    if supabase_uploader.is_configured():
        storage_uri = await supabase_uploader.upload_flac(
            local_path=local_path,
            region=DEFAULT_REGION,
            organization_id=organization_id,
            meeting_id=meeting_id,
        )
    elif r2_uploader.is_configured():
        storage_uri = await r2_uploader.upload_flac(
            local_path=local_path,
            region=DEFAULT_REGION,
            organization_id=organization_id,
            meeting_id=meeting_id,
        )
    else:
        # Single-host fallback (docker-compose with shared volume)
        storage_uri = str(file_path)
        logger.warning(
            "Neither Supabase Storage nor R2 configured — falling back to "
            "local path %s. The API will only be able to read this if it "
            "shares /tmp/vaktram with the bot.",
            storage_uri,
        )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_URL}/internal/meetings/{meeting_id}/audio-ready",
            json={"audio_storage_path": storage_uri, "user_id": user_id},
        )
        resp.raise_for_status()

    logger.info(
        "API notified: audio ready for meeting %s (%s, %d bytes) -> %s",
        meeting_id, file_path.name, file_path.stat().st_size, storage_uri,
    )
    return storage_uri
