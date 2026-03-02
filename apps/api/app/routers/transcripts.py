"""Transcript endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.schemas.transcript import (
    FullTranscript,
    TranscriptBulkCreate,
    TranscriptSegmentRead,
)
from app.services.transcript_service import TranscriptService

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.get("/{meeting_id}", response_model=FullTranscript)
async def get_transcript(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get the full transcript for a meeting."""
    service = TranscriptService(db)
    transcript = await service.get_transcript(meeting_id=meeting_id, user_id=user.id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript


@router.post("", response_model=list[TranscriptSegmentRead], status_code=status.HTTP_201_CREATED)
async def ingest_transcript(
    payload: TranscriptBulkCreate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Bulk-insert transcript segments for a meeting."""
    service = TranscriptService(db)
    return await service.bulk_create(
        meeting_id=payload.meeting_id,
        segments=payload.segments,
        user_id=user.id,
    )


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcript(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Delete all transcript segments for a meeting."""
    service = TranscriptService(db)
    await service.delete_transcript(meeting_id=meeting_id, user_id=user.id)
