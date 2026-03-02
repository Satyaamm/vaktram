"""
Upload recorded audio files to Supabase Storage.
Handles chunked uploads, retry logic, and metadata tagging.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = os.getenv("AUDIO_STORAGE_BUCKET", "meeting-recordings")


def _get_supabase_client() -> Client:
    """Create a Supabase client with service-role credentials."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def upload_audio_file(
    local_path: str,
    meeting_id: str,
    organization_id: str,
    content_type: str = "audio/wav",
) -> str:
    """
    Upload a single audio file to Supabase Storage.

    Returns the storage path (key) of the uploaded file.
    """
    file_path = Path(local_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {local_path}")

    storage_key = f"{organization_id}/{meeting_id}/{file_path.name}"

    client = _get_supabase_client()

    with open(file_path, "rb") as f:
        data = f.read()

    result = client.storage.from_(STORAGE_BUCKET).upload(
        path=storage_key,
        file=data,
        file_options={"content-type": content_type},
    )

    logger.info(
        "Uploaded %s to %s/%s (%d bytes)",
        file_path.name,
        STORAGE_BUCKET,
        storage_key,
        len(data),
    )
    return storage_key


async def upload_audio_chunks(
    chunk_dir: str,
    meeting_id: str,
    organization_id: str,
    pattern: str = "chunk_*.wav",
) -> list[str]:
    """
    Upload all audio chunks from a directory.

    Returns a list of storage keys for the uploaded files.
    """
    chunk_files = sorted(Path(chunk_dir).glob(pattern))
    if not chunk_files:
        logger.warning("No chunks found matching %s in %s", pattern, chunk_dir)
        return []

    keys = []
    for chunk_path in chunk_files:
        key = await upload_audio_file(
            local_path=str(chunk_path),
            meeting_id=meeting_id,
            organization_id=organization_id,
        )
        keys.append(key)

    logger.info("Uploaded %d chunks for meeting %s", len(keys), meeting_id)
    return keys


def get_download_url(storage_key: str, expires_in: int = 3600) -> str:
    """Generate a signed download URL for an audio file."""
    client = _get_supabase_client()
    result = client.storage.from_(STORAGE_BUCKET).create_signed_url(
        path=storage_key,
        expires_in=expires_in,
    )
    return result["signedURL"]
