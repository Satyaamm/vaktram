"""Retention enforcement: per-org policies + a daily purge job.

Run via the scheduler: enumerate orgs with retention_policies, drop meetings
(and cascading transcript/summary/embedding rows) older than the policy. Audio
in object storage gets purged via a separate hook so we don't block the DB
transaction on S3.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import RetentionPolicy
from app.models.meeting import Meeting

logger = logging.getLogger(__name__)


async def purge_expired(db: AsyncSession, *, default_days: int) -> int:
    """Delete meetings that exceed their org's retention. Returns row count."""
    now = datetime.now(timezone.utc)

    # 1) Honor per-org policies first.
    policies = (
        await db.execute(select(RetentionPolicy).where(RetentionPolicy.legal_hold.is_(False)))
    ).scalars().all()
    purged = 0
    for p in policies:
        cutoff = now - timedelta(days=p.default_days)
        purged += await _purge_org(db, p.organization_id, cutoff)

    # 2) Orgs without an explicit policy fall back to platform default.
    orgs_with_policy = {p.organization_id for p in policies}
    rows = (
        await db.execute(
            select(Meeting.organization_id, Meeting.id, Meeting.created_at)
            .where(Meeting.created_at < now - timedelta(days=default_days))
        )
    ).all()
    for org_id, meeting_id, _ in rows:
        if org_id in orgs_with_policy:
            continue
        m = await db.get(Meeting, meeting_id)
        if m:
            await db.delete(m)
            purged += 1
    return purged


async def _purge_org(
    db: AsyncSession, organization_id: uuid.UUID, cutoff: datetime
) -> int:
    rows = (
        await db.execute(
            select(Meeting.id)
            .where(Meeting.organization_id == organization_id)
            .where(Meeting.created_at < cutoff)
        )
    ).all()
    n = 0
    for (mid,) in rows:
        m = await db.get(Meeting, mid)
        if m:
            await db.delete(m)
            n += 1
    return n
