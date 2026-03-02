"""Bot control endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.services.bot_service import BotService

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
