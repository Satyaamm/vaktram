"""Meeting analytics endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import TranscriptSegment
from app.models.summary import MeetingSummary
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
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
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


class UsageResponse(BaseModel):
    meetings_this_month: int
    storage_used_mb: float
    plan: str


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get current month usage for the authenticated user."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    q = select(func.count()).select_from(
        select(Meeting)
        .where(Meeting.user_id == user.id, Meeting.created_at >= month_start)
        .subquery()
    )
    result = await db.execute(q)
    meetings_this_month = result.scalar() or 0

    return UsageResponse(
        meetings_this_month=meetings_this_month,
        storage_used_mb=0.0,
        plan="free",
    )


class SpeakerTalkTimeItem(BaseModel):
    speaker_name: str
    total_seconds: float
    meeting_count: int
    percentage: float


@router.get("/talk-time", response_model=list[SpeakerTalkTimeItem])
async def get_talk_time(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get speaker talk-time breakdown for the user's meetings."""
    q = (
        select(
            TranscriptSegment.speaker_name,
            func.sum(TranscriptSegment.end_time - TranscriptSegment.start_time).label("total_seconds"),
            func.count(func.distinct(TranscriptSegment.meeting_id)).label("meeting_count"),
        )
        .join(Meeting, Meeting.id == TranscriptSegment.meeting_id)
        .where(Meeting.user_id == user.id)
        .group_by(TranscriptSegment.speaker_name)
        .order_by(func.sum(TranscriptSegment.end_time - TranscriptSegment.start_time).desc())
        .limit(20)
    )
    result = await db.execute(q)
    rows = result.all()
    total = sum(r.total_seconds for r in rows) or 1
    return [
        SpeakerTalkTimeItem(
            speaker_name=r.speaker_name,
            total_seconds=round(r.total_seconds, 1),
            meeting_count=r.meeting_count,
            percentage=round((r.total_seconds / total) * 100, 1),
        )
        for r in rows
    ]


class MeetingFrequencyItem(BaseModel):
    date: str
    count: int


@router.get("/frequency", response_model=list[MeetingFrequencyItem])
async def get_frequency(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get meeting frequency over time."""
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    start = datetime.now(timezone.utc) - timedelta(days=days)
    q = (
        select(
            cast(Meeting.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(Meeting.user_id == user.id, Meeting.created_at >= start)
        .group_by(cast(Meeting.created_at, Date))
        .order_by(cast(Meeting.created_at, Date))
    )
    result = await db.execute(q)
    return [
        MeetingFrequencyItem(date=str(r.date), count=r.count)
        for r in result.all()
    ]


class TopicFrequencyItem(BaseModel):
    topic: str
    count: int


@router.get("/topics", response_model=list[TopicFrequencyItem])
async def get_topics(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get topic frequency from meeting summaries."""
    q = (
        select(MeetingSummary.topics)
        .join(Meeting, Meeting.id == MeetingSummary.meeting_id)
        .where(Meeting.user_id == user.id, MeetingSummary.topics.isnot(None))
    )
    result = await db.execute(q)
    topic_counts: dict[str, int] = {}
    for (topics,) in result.all():
        if isinstance(topics, list):
            for t in topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    return [TopicFrequencyItem(topic=t, count=c) for t, c in sorted_topics]
