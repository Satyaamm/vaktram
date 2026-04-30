"""Topic Tracker scanner.

Runs at the end of the transcribe stage. For each active tracker in an org,
walk the new transcript segments and persist a TopicHit for every keyword
match (case-insensitive substring). Optionally fan out an email digest to
`notify_emails` when at least one hit is found.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intel import TopicHit, TopicTracker
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.services import email_service

logger = logging.getLogger(__name__)


async def scan_meeting(db: AsyncSession, meeting_id: uuid.UUID) -> int:
    """Match every active tracker in the meeting's org against its segments.

    Returns the number of hits recorded. Caller commits.
    """
    meeting = await db.get(Meeting, meeting_id)
    if meeting is None or not meeting.organization_id:
        return 0

    trackers = (
        await db.execute(
            select(TopicTracker)
            .where(TopicTracker.organization_id == meeting.organization_id)
            .where(TopicTracker.is_active.is_(True))
        )
    ).scalars().all()
    if not trackers:
        return 0

    segments = (
        await db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.start_time.asc())
        )
    ).scalars().all()
    if not segments:
        return 0

    hits_by_tracker: dict[uuid.UUID, list[TopicHit]] = {}
    total = 0
    for tracker in trackers:
        keywords = [k.lower() for k in (tracker.keywords or []) if k]
        if not keywords:
            continue
        for seg in segments:
            content_lower = (seg.content or "").lower()
            for kw in keywords:
                if kw in content_lower:
                    hit = TopicHit(
                        tracker_id=tracker.id,
                        meeting_id=meeting_id,
                        segment_id=seg.id,
                        matched_keyword=kw,
                        snippet=(seg.content or "")[:500],
                        timestamp_seconds=seg.start_time,
                    )
                    db.add(hit)
                    hits_by_tracker.setdefault(tracker.id, []).append(hit)
                    total += 1
                    break  # one hit per segment per tracker is enough

    await db.flush()

    # Email digest (best-effort, no transactional guarantee)
    for tracker in trackers:
        hits = hits_by_tracker.get(tracker.id) or []
        if not hits or not tracker.notify_emails:
            continue
        body_lines = [
            f"<li><b>{h.matched_keyword}</b> @{int(h.timestamp_seconds or 0)}s — "
            f"{h.snippet[:200]}</li>"
            for h in hits
        ]
        html = (
            f"<h3>Topic Tracker: {tracker.name}</h3>"
            f"<p>Mentioned in meeting <b>{meeting.title}</b>:</p>"
            f"<ul>{''.join(body_lines)}</ul>"
        )
        for to in tracker.notify_emails:
            await email_service.send_email(
                to=to,
                subject=f"[Vaktram] '{tracker.name}' mentioned in {meeting.title}",
                html=html,
            )

    return total
