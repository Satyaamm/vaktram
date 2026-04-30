"""URI parsing for the storage adapter — pure functions, no network."""

from __future__ import annotations

import pytest

from app.services import r2_storage_service as r2


def test_parse_r2_uri():
    bucket, key = r2._parse_uri("r2://vaktram-audio/us-east-1/org/abc/m.flac")
    assert bucket == "vaktram-audio"
    assert key == "us-east-1/org/abc/m.flac"


def test_parse_s3_uri():
    bucket, key = r2._parse_uri("s3://my-bucket/path/to/audio.flac")
    assert bucket == "my-bucket"
    assert key == "path/to/audio.flac"


def test_audio_key_shape():
    import uuid

    org = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mid = uuid.UUID("22222222-2222-2222-2222-222222222222")
    key = r2.audio_key(region="eu-west-1", organization_id=org, meeting_id=mid)
    assert key.startswith("eu-west-1/org/")
    assert "/meetings/" in key
    assert key.endswith("/audio.flac")


@pytest.mark.asyncio
async def test_fetch_bytes_local_path(tmp_path):
    p = tmp_path / "recording.flac"
    p.write_bytes(b"fakeflac")
    blob = await r2.fetch_bytes(str(p))
    assert blob == b"fakeflac"
