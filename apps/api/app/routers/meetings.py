"""CRUD meetings router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.schemas.meeting import MeetingCreate, MeetingList, MeetingRead, MeetingUpdate
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=MeetingList)
async def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List meetings for the authenticated user."""
    service = MeetingService(db)
    return await service.list_meetings(
        user_id=user.id, page=page, page_size=page_size, status_filter=status_filter
    )


@router.post("", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Create a new meeting."""
    service = MeetingService(db)
    return await service.create_meeting(user_id=user.id, data=payload)


@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get a single meeting by ID."""
    service = MeetingService(db)
    meeting = await service.get_meeting(meeting_id=meeting_id, user_id=user.id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingRead)
async def update_meeting(
    meeting_id: uuid.UUID,
    payload: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Update a meeting."""
    service = MeetingService(db)
    meeting = await service.update_meeting(
        meeting_id=meeting_id, user_id=user.id, data=payload
    )
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Delete a meeting."""
    service = MeetingService(db)
    deleted = await service.delete_meeting(meeting_id=meeting_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
