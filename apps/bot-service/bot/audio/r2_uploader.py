"""Cloudflare R2 audio uploader for the bot service.

Bot pods on Fly.io don't share a filesystem with the API pods, so we can't
hand off audio via a shared volume. Instead the bot uploads the FLAC blob
directly to R2 (S3-compatible, zero egress) and the API reads it from there.

R2 is configured by setting these env vars on the bot service:
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET

If any are missing we fall back to the legacy local-file path so docker-compose
still works on a single host.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return all(
        os.getenv(k)
        for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    )


def _client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def object_key(
    *,
    region: str,
    organization_id: Optional[str],
    meeting_id: str,
) -> str:
    org_part = organization_id or "no-org"
    return f"{region}/org/{org_part}/meetings/{meeting_id}/audio.flac"


async def upload_flac(
    local_path: str,
    *,
    region: str,
    organization_id: Optional[str],
    meeting_id: str,
) -> str:
    """Upload a FLAC file to R2. Returns the storage URI we record in the
    Meeting row — `r2://<bucket>/<key>` — which the API uses to fetch it.
    """
    import asyncio

    bucket = os.getenv("R2_BUCKET", "vaktram-audio")
    key = object_key(region=region, organization_id=organization_id, meeting_id=meeting_id)

    def _put() -> None:
        _client().upload_file(
            Filename=local_path,
            Bucket=bucket,
            Key=key,
            ExtraArgs={"ContentType": "audio/flac"},
        )

    await asyncio.to_thread(_put)
    uri = f"r2://{bucket}/{key}"
    logger.info("Uploaded %s -> %s", local_path, uri)
    return uri
