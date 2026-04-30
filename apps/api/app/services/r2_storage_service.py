"""Cloudflare R2 audio storage.

R2 speaks the S3 API, so we use boto3. Set R2_ACCOUNT_ID + R2_ACCESS_KEY_ID +
R2_SECRET_ACCESS_KEY in env. Bot-service uploads via presigned PUT and the
API generates presigned GETs for transcribe/summarize. R2 has zero egress
fees so this is dramatically cheaper than S3 or Supabase Storage for audio.

The adapter no-ops gracefully when R2 isn't configured — falls back to local
filesystem under /tmp/vaktram so docker-compose still works.
"""

from __future__ import annotations

import logging
import os
import uuid

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


def _r2_endpoint() -> str | None:
    account = os.getenv("R2_ACCOUNT_ID")
    if not account:
        return None
    return f"https://{account}.r2.cloudflarestorage.com"


def is_configured() -> bool:
    return bool(
        os.getenv("R2_ACCOUNT_ID")
        and os.getenv("R2_ACCESS_KEY_ID")
        and os.getenv("R2_SECRET_ACCESS_KEY")
    )


def _client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=_r2_endpoint(),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def audio_key(*, region: str, organization_id: uuid.UUID, meeting_id: uuid.UUID) -> str:
    return f"{region}/org/{organization_id}/meetings/{meeting_id}/audio.flac"


def presigned_put(key: str, content_type: str = "audio/flac", expires: int = 3600) -> str:
    """Return a URL the bot-service can PUT bytes directly to."""
    if not is_configured():
        raise RuntimeError("R2 not configured")
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": _settings.storage_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presigned_get(key: str, expires: int = 3600) -> str:
    if not is_configured():
        raise RuntimeError("R2 not configured")
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _settings.storage_bucket, "Key": key},
        ExpiresIn=expires,
    )


async def fetch_bytes(uri_or_path: str) -> bytes:
    """Download audio bytes from any supported source.

    Accepts:
      r2://bucket/key   — Cloudflare R2
      s3://bucket/key   — any S3-compatible (resolved via the same client)
      /abs/path         — local filesystem (compose / single-host)
    """
    if uri_or_path.startswith(("r2://", "s3://")):
        bucket, key = _parse_uri(uri_or_path)
        import asyncio
        return await asyncio.to_thread(_get_blocking, bucket, key)

    # Local file fallback for docker-compose / single-host installs
    with open(uri_or_path, "rb") as f:
        return f.read()


def _parse_uri(uri: str) -> tuple[str, str]:
    # r2://bucket/path/to/object.flac
    rest = uri.split("://", 1)[1]
    bucket, _, key = rest.partition("/")
    return bucket, key


def _get_blocking(bucket: str, key: str) -> bytes:
    if not is_configured():
        raise RuntimeError("R2 not configured but tried to fetch r2:// URI")
    obj = _client().get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()
