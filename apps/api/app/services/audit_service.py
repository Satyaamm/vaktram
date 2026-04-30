"""Tamper-evident audit logging.

Each row stores the SHA-256 hash of the previous row's hash chained with the
current row's canonical JSON. A break in the chain proves tampering. The
hourly export job ships rows to the audit_export_bucket with S3 Object Lock.

Schema note: AuditLog already has `details` (JSONB). We piggy-back on it for
the hash columns to avoid another migration churn — `details.prev_hash` and
`details.row_hash`. A future migration can promote them to first-class
columns once the access patterns settle.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import AuditLog

logger = logging.getLogger(__name__)
GENESIS = "0" * 64  # SHA-256 placeholder for the first row in the chain


async def record(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    organization_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    ip_address: str | None,
    user_agent: str | None = None,
    extra: dict | None = None,
) -> AuditLog:
    """Append an audit row, hash-chained from the previous row."""
    prev = (
        await db.execute(
            select(AuditLog).order_by(desc(AuditLog.created_at)).limit(1)
        )
    ).scalar_one_or_none()
    prev_hash = (
        (prev.details or {}).get("row_hash", GENESIS) if prev else GENESIS
    )

    body = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id) if user_id else None,
        "organization_id": str(organization_id) if organization_id else None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip": ip_address,
        "ua": user_agent,
        "extra": extra or {},
        "prev_hash": prev_hash,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    row_hash = hashlib.sha256(canonical.encode()).hexdigest()
    body["row_hash"] = row_hash

    row = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=body,
        ip_address=ip_address,
    )
    db.add(row)
    await db.flush()
    return row


async def verify_chain(db: AsyncSession, limit: int = 10_000) -> dict:
    """Walk the most-recent N rows and verify the hash chain."""
    rows = (
        await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.asc()).limit(limit)
        )
    ).scalars().all()

    expected_prev = GENESIS
    breaks: list[str] = []
    for row in rows:
        details = row.details or {}
        body = {k: v for k, v in details.items() if k != "row_hash"}
        body["prev_hash"] = expected_prev
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        recomputed = hashlib.sha256(canonical.encode()).hexdigest()
        if recomputed != details.get("row_hash"):
            breaks.append(str(row.id))
        expected_prev = details.get("row_hash", expected_prev)
    return {"checked": len(rows), "breaks": breaks, "ok": not breaks}
