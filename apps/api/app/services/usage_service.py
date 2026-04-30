"""Record and query usage events.

`record()` is fire-and-forget from request handlers and pipeline workers.
`current_period_total()` is read by the quota middleware and the billing UI.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import UsageEvent, UsageKind

logger = logging.getLogger(__name__)


async def record(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    kind: UsageKind,
    quantity: int,
    user_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    """Append a usage event. Caller commits the session."""
    if quantity <= 0:
        return
    db.add(
        UsageEvent(
            organization_id=organization_id,
            user_id=user_id,
            meeting_id=meeting_id,
            kind=kind,
            quantity=quantity,
            metadata_=metadata,
        )
    )


async def current_period_total(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    kind: UsageKind,
    period_start: datetime | None = None,
) -> int:
    """Sum events for the current calendar month (or a custom window)."""
    if period_start is None:
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stmt = select(func.coalesce(func.sum(UsageEvent.quantity), 0)).where(
        UsageEvent.organization_id == organization_id,
        UsageEvent.kind == kind,
        UsageEvent.created_at >= period_start,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())
