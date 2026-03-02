"""Internal API endpoints for pipeline callbacks. Called by bot-service and workers."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/internal", tags=["internal"])


# ── Request schemas ──────────────────────────────────────────────────────

class AudioReadyRequest(BaseModel):
    """Sent by bot-service when audio upload is complete."""

    audio_storage_path: str = Field(..., description="Supabase Storage path for the audio file")
    user_id: uuid.UUID = Field(..., description="Owner of the meeting")


class TranscriptionCompleteRequest(BaseModel):
    """Sent by transcription worker when done."""

    segment_count: int = Field(..., ge=0, description="Number of transcript segments produced")


class SummarizationCompleteRequest(BaseModel):
    """Sent by summarization worker when done."""

    pass  # No extra data needed; meeting_id is in the URL


class PipelineErrorRequest(BaseModel):
    """Sent by any worker on failure."""

    stage: str = Field(..., description="Pipeline stage that failed (e.g. transcription, summarization)")
    error: str = Field(..., description="Human-readable error message")


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/meetings/{meeting_id}/audio-ready")
async def audio_ready(
    meeting_id: uuid.UUID,
    body: AudioReadyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Called by bot service when audio upload is complete."""
    pipeline = PipelineService(db)
    await pipeline.on_audio_ready(
        meeting_id=meeting_id,
        audio_storage_path=body.audio_storage_path,
        user_id=body.user_id,
    )
    return {"status": "ok", "next_stage": "transcribing"}


@router.post("/meetings/{meeting_id}/transcription-complete")
async def transcription_complete(
    meeting_id: uuid.UUID,
    body: TranscriptionCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Called by transcription worker when done."""
    pipeline = PipelineService(db)
    await pipeline.on_transcription_complete(
        meeting_id=meeting_id,
        segment_count=body.segment_count,
    )
    return {"status": "ok", "next_stage": "summarizing"}


@router.post("/meetings/{meeting_id}/summarization-complete")
async def summarization_complete(
    meeting_id: uuid.UUID,
    body: SummarizationCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Called by summarization worker when done."""
    pipeline = PipelineService(db)
    await pipeline.on_summarization_complete(meeting_id=meeting_id)
    return {"status": "ok", "next_stage": "done"}


@router.post("/meetings/{meeting_id}/pipeline-error")
async def pipeline_error(
    meeting_id: uuid.UUID,
    body: PipelineErrorRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Called by any worker on failure."""
    pipeline = PipelineService(db)
    await pipeline.on_pipeline_error(
        meeting_id=meeting_id,
        stage=body.stage,
        error=body.error,
    )
    return {"status": "ok", "stage": body.stage, "result": "failed"}
