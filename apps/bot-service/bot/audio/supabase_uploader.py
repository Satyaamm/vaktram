"""Upload audio FLAC to Supabase Storage via the REST API.

Why this exists:
* The bot runs on a VPS / laptop separate from the API. There's no shared
  filesystem, so the original "send a path" handshake doesn't work.
* Supabase Storage exposes a plain S3-compatible REST API; we just POST the
  bytes with the service-role key and get back an object path.
* The API stores `supabase://bucket/key` URIs and `r2_storage_service.fetch_bytes`
  knows how to resolve them at transcription time.

Set on the bot host:
  SUPABASE_URL=https://<project>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
  STORAGE_BUCKET=vaktram-audio   (default)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def object_key(
    *,
    region: str,
    organization_id: Optional[str],
    meeting_id: str,
) -> str:
    org = organization_id or "no-org"
    return f"{region}/org/{org}/meetings/{meeting_id}/audio.flac"


async def upload_flac(
    local_path: str,
    *,
    region: str,
    organization_id: Optional[str],
    meeting_id: str,
) -> str:
    """Upload the FLAC file and return the `supabase://bucket/key` URI."""
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    bucket = os.getenv("STORAGE_BUCKET", "vaktram-audio")
    obj_key = object_key(
        region=region, organization_id=organization_id, meeting_id=meeting_id
    )

    with open(local_path, "rb") as f:
        body = f.read()

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{base}/storage/v1/object/{bucket}/{obj_key}",
            content=body,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "audio/flac",
                "x-upsert": "true",  # allow re-uploads on retry
            },
        )
        if resp.status_code >= 300:
            raise RuntimeError(
                f"Supabase Storage upload failed: HTTP {resp.status_code} — {resp.text[:300]}"
            )

    uri = f"supabase://{bucket}/{obj_key}"
    logger.info("Uploaded %s -> %s (%d bytes)", local_path, uri, len(body))
    return uri
