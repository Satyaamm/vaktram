"""Bot control endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.meeting import Meeting
from app.models.scheduler import ScheduledJob
from app.models.team import UserProfile
from app.services.bot_service import BotService
from app.services.meeting_scheduler import schedule_bot_deploy

router = APIRouter(prefix="/bot", tags=["bot"])


class BotJoinRequest(BaseModel):
    meeting_id: uuid.UUID
    meeting_url: str | None = Field(None, description="Override meeting URL")


class BotStatusResponse(BaseModel):
    meeting_id: uuid.UUID
    bot_id: str | None
    status: str
    message: str


@router.post("/join", response_model=BotStatusResponse)
async def join_meeting(
    payload: BotJoinRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Send a recording bot to join a meeting."""
    service = BotService(db)
    return await service.join_meeting(
        meeting_id=payload.meeting_id,
        user_id=user.id,
        meeting_url_override=payload.meeting_url,
    )


@router.post("/leave/{meeting_id}", response_model=BotStatusResponse)
async def leave_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Remove the bot from a meeting."""
    service = BotService(db)
    return await service.leave_meeting(meeting_id=meeting_id, user_id=user.id)


@router.get("/status/{meeting_id}", response_model=BotStatusResponse)
async def bot_status(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get the current bot status for a meeting."""
    service = BotService(db)
    return await service.get_status(meeting_id=meeting_id, user_id=user.id)


class ScheduleBotRequest(BaseModel):
    meeting_id: uuid.UUID
    deploy_at: datetime | None = Field(None, description="When to deploy. Defaults to 30s before meeting start.")


class ScheduledJobRead(BaseModel):
    id: uuid.UUID
    job_type: str
    meeting_id: uuid.UUID | None
    scheduled_at: datetime
    executed_at: datetime | None
    status: str
    result: str | None
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/schedule", response_model=ScheduledJobRead, status_code=status.HTTP_201_CREATED)
async def schedule_bot(
    payload: ScheduleBotRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Schedule a bot to join a meeting at a specific time."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == payload.meeting_id, Meeting.user_id == user.id)
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.meeting_url:
        raise HTTPException(status_code=400, detail="Meeting has no URL")

    deploy_at = payload.deploy_at
    if not deploy_at:
        if meeting.scheduled_start:
            deploy_at = meeting.scheduled_start - timedelta(seconds=30)
        else:
            deploy_at = datetime.now(timezone.utc)

    job = await schedule_bot_deploy(
        meeting_id=meeting.id,
        user_id=user.id,
        deploy_at=deploy_at,
        meeting_url=meeting.meeting_url,
        platform=meeting.platform.value if meeting.platform else "google_meet",
        organization_id=meeting.organization_id,
        db=db,
    )
    return job


@router.get("/scheduled-jobs", response_model=list[ScheduledJobRead])
async def list_scheduled_jobs(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List scheduled jobs for the current user."""
    query = select(ScheduledJob).where(
        ScheduledJob.user_id == user.id
    ).order_by(ScheduledJob.scheduled_at.desc())

    if status_filter:
        query = query.where(ScheduledJob.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()
