"""Soundbites — clip + share short audio segments from a meeting."""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.intel import Soundbite
from app.models.meeting import Meeting
from app.models.team import UserProfile

router = APIRouter(prefix="/soundbites", tags=["soundbites"])


class SoundbiteCreate(BaseModel):
    meeting_id: uuid.UUID
    start_seconds: float = Field(..., ge=0)
    end_seconds: float = Field(..., gt=0)
    title: str | None = None
    transcript: str | None = None


@router.post("")
async def create_soundbite(
    body: SoundbiteCreate,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.end_seconds <= body.start_seconds:
        raise HTTPException(400, "end_seconds must be > start_seconds")
    meeting = await db.get(Meeting, body.meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.user_id != user.id and meeting.organization_id != user.organization_id:
        raise HTTPException(403, "No access to this meeting")
    sb = Soundbite(
        meeting_id=body.meeting_id,
        user_id=user.id,
        title=body.title,
        start_seconds=body.start_seconds,
        end_seconds=body.end_seconds,
        transcript=body.transcript,
        share_token=secrets.token_urlsafe(16),
    )
    db.add(sb)
    await db.flush()
    return {
        "id": str(sb.id),
        "share_token": sb.share_token,
        "share_url": f"/s/{sb.share_token}",
    }


@router.get("/by-meeting/{meeting_id}")
async def list_for_meeting(
    meeting_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Soundbite)
        .where(Soundbite.meeting_id == meeting_id)
        .order_by(Soundbite.created_at.desc())
    )).scalars().all()
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "start": s.start_seconds,
            "end": s.end_seconds,
            "transcript": s.transcript,
            "share_url": f"/s/{s.share_token}" if s.share_token else None,
        }
        for s in rows
    ]


@router.get("/shared/{share_token}")
async def public_soundbite(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public share endpoint — no auth, only the snippet content."""
    rows = await db.execute(select(Soundbite).where(Soundbite.share_token == share_token))
    sb = rows.scalar_one_or_none()
    if not sb:
        raise HTTPException(404, "Not found")
    return {
        "title": sb.title,
        "start": sb.start_seconds,
        "end": sb.end_seconds,
        "transcript": sb.transcript,
    }
