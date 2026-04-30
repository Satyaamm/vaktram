"""Dead-letter helpers used by pipeline workers and the admin replay tool."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import DeadLetterJob, JobStatus

logger = logging.getLogger(__name__)


async def record_dead_letter(
    db: AsyncSession,
    *,
    kind: str,
    payload: dict,
    error: str,
    attempts: int,
    organization_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None,
) -> DeadLetterJob:
    job = DeadLetterJob(
        organization_id=organization_id,
        meeting_id=meeting_id,
        kind=kind,
        payload=payload,
        error=error,
        attempts=attempts,
        status=JobStatus.dead_letter,
        last_attempt_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    logger.error("DLQ recorded kind=%s meeting=%s err=%s", kind, meeting_id, error)
    return job


async def list_dead(db: AsyncSession, limit: int = 100) -> list[DeadLetterJob]:
    rows = await db.execute(
        select(DeadLetterJob)
        .where(DeadLetterJob.status == JobStatus.dead_letter)
        .order_by(DeadLetterJob.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars().all())
