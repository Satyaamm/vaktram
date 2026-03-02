"""Meeting analytics endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.team import UserProfile

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsOverview(BaseModel):
    total_meetings: int
    completed_meetings: int
    total_duration_hours: float
    avg_duration_minutes: float
    meetings_this_week: int


class SpeakerStat(BaseModel):
    speaker_name: str
    total_speaking_seconds: int
    segment_count: int


class MeetingAnalytics(BaseModel):
    overview: AnalyticsOverview
    top_speakers: list[SpeakerStat]


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get high-level analytics for the authenticated user."""
    base = select(Meeting).where(Meeting.user_id == user.id)

    total_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(total_q)
    total_meetings = total_result.scalar() or 0

    completed_q = select(func.count()).select_from(
        base.where(Meeting.status == MeetingStatus.completed).subquery()
    )
    completed_result = await db.execute(completed_q)
    completed_meetings = completed_result.scalar() or 0

    duration_q = select(
        func.coalesce(func.sum(Meeting.duration_seconds), 0),
        func.coalesce(func.avg(Meeting.duration_seconds), 0),
    ).where(Meeting.user_id == user.id, Meeting.duration_seconds.isnot(None))
    dur_result = await db.execute(duration_q)
    dur_row = dur_result.one()
    total_duration_seconds = dur_row[0] or 0
    avg_duration_seconds = dur_row[1] or 0

    # Meetings this week (last 7 days)
    from datetime import timedelta

    week_ago = datetime.utcnow() - timedelta(days=7)
    week_q = select(func.count()).select_from(
        base.where(Meeting.created_at >= week_ago).subquery()
    )
    week_result = await db.execute(week_q)
    meetings_this_week = week_result.scalar() or 0

    return AnalyticsOverview(
        total_meetings=total_meetings,
        completed_meetings=completed_meetings,
        total_duration_hours=round(total_duration_seconds / 3600, 2),
        avg_duration_minutes=round(avg_duration_seconds / 60, 2),
        meetings_this_week=meetings_this_week,
    )
