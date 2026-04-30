"""Topic Tracker management + hits feed."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.intel import TopicHit, TopicTracker
from app.models.team import UserProfile

router = APIRouter(prefix="/topics", tags=["topics"])


class TrackerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    keywords: list[str] = Field(..., min_length=1)
    notify_emails: list[str] = []


class TrackerUpdate(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
    notify_emails: list[str] | None = None
    is_active: bool | None = None


@router.get("")
async def list_trackers(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        return []
    rows = (await db.execute(
        select(TopicTracker)
        .where(TopicTracker.organization_id == user.organization_id)
        .order_by(TopicTracker.created_at.desc())
    )).scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "keywords": t.keywords,
            "is_active": t.is_active,
            "notify_emails": t.notify_emails,
        }
        for t in rows
    ]


@router.post("")
async def create_tracker(
    body: TrackerCreate,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No organization")
    tracker = TopicTracker(
        organization_id=user.organization_id,
        name=body.name,
        keywords=[k.strip() for k in body.keywords if k.strip()],
        notify_emails=body.notify_emails,
    )
    db.add(tracker)
    await db.flush()
    return {"id": str(tracker.id)}


@router.patch("/{tracker_id}")
async def update_tracker(
    tracker_id: uuid.UUID,
    body: TrackerUpdate,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tracker = await db.get(TopicTracker, tracker_id)
    if not tracker or tracker.organization_id != user.organization_id:
        raise HTTPException(404, "Tracker not found")
    if body.name is not None:
        tracker.name = body.name
    if body.keywords is not None:
        tracker.keywords = [k.strip() for k in body.keywords if k.strip()]
    if body.notify_emails is not None:
        tracker.notify_emails = body.notify_emails
    if body.is_active is not None:
        tracker.is_active = body.is_active
    await db.flush()
    return {"ok": True}


@router.delete("/{tracker_id}", status_code=204)
async def delete_tracker(
    tracker_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tracker = await db.get(TopicTracker, tracker_id)
    if not tracker or tracker.organization_id != user.organization_id:
        raise HTTPException(404, "Tracker not found")
    await db.delete(tracker)
    await db.flush()
    return


@router.get("/{tracker_id}/hits")
async def list_hits(
    tracker_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    tracker = await db.get(TopicTracker, tracker_id)
    if not tracker or tracker.organization_id != user.organization_id:
        raise HTTPException(404, "Tracker not found")
    rows = (await db.execute(
        select(TopicHit)
        .where(TopicHit.tracker_id == tracker_id)
        .order_by(desc(TopicHit.created_at))
        .limit(limit)
    )).scalars().all()
    return [
        {
            "id": str(h.id),
            "meeting_id": str(h.meeting_id),
            "matched_keyword": h.matched_keyword,
            "snippet": h.snippet,
            "timestamp": h.timestamp_seconds,
            "created_at": h.created_at,
        }
        for h in rows
    ]
