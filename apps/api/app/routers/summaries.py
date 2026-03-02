"""Summary endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.schemas.summary import SummaryGenerateRequest, SummaryRead
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/{meeting_id}", response_model=SummaryRead)
async def get_summary(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get the summary for a meeting."""
    service = SummaryService(db)
    summary = await service.get_summary(meeting_id=meeting_id, user_id=user.id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.post("/generate", response_model=SummaryRead)
async def generate_summary(
    payload: SummaryGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Generate an AI summary for a meeting."""
    service = SummaryService(db)
    return await service.generate_summary(
        meeting_id=payload.meeting_id,
        user=user,
        provider=payload.provider,
        model=payload.model,
        custom_prompt=payload.custom_prompt,
    )


@router.delete("/{meeting_id}", status_code=204)
async def delete_summary(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Delete the summary for a meeting."""
    service = SummaryService(db)
    deleted = await service.delete_summary(meeting_id=meeting_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Summary not found")
