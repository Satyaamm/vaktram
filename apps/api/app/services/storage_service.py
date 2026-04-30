"""Region-aware storage paths.

Every audio/transcript/export object is namespaced under
`{region}/org/{organization_id}/...`. The bucket selection is per-region so
EU-pinned orgs never write into a US bucket and vice-versa. Lifecycle rules
on each bucket (set in Terraform/Helm) enforce retention defaults.
"""

from __future__ import annotations

import uuid

from app.config import get_settings

_settings = get_settings()

# Map region → bucket. Override via REGIONAL_BUCKETS env (JSON) for prod.
REGIONAL_BUCKETS = {
    "us-east-1": _settings.storage_bucket,
    "us-west-2": f"{_settings.storage_bucket}-usw2",
    "eu-west-1": f"{_settings.storage_bucket}-euw1",
    "ap-south-1": f"{_settings.storage_bucket}-aps1",
}


def bucket_for(region: str) -> str:
    return REGIONAL_BUCKETS.get(region, _settings.storage_bucket)


def audio_path(*, region: str, organization_id: uuid.UUID, meeting_id: uuid.UUID) -> str:
    return f"{region}/org/{organization_id}/meetings/{meeting_id}/audio.flac"


def transcript_path(*, region: str, organization_id: uuid.UUID, meeting_id: uuid.UUID) -> str:
    return f"{region}/org/{organization_id}/meetings/{meeting_id}/transcript.json"


def export_path(*, region: str, organization_id: uuid.UUID, request_id: uuid.UUID) -> str:
    return f"{region}/org/{organization_id}/exports/{request_id}.zip"
