"""Internal API endpoints for pipeline processing.

These endpoints are called by QStash (job queue) or directly for local dev.
They do NOT require user auth — they are protected by QStash signature verification.
"""

from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func as sa_func

from app.config import get_settings
from app.dependencies import get_db
from app.models.billing import UsageKind
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import TranscriptSegment
from app.services import usage_service
from app.services.pipeline_service import PipelineService
from app.services.transcription_service import transcribe_audio
from app.services.summarization_service import summarize_meeting
from app.services.queue_service import publish_job
from app.utils.internal_auth import require_internal_auth
from app.utils.qstash_signature import verify_qstash_signature

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


async def _run_diarization(audio_bytes: bytes, filename: str) -> list[dict] | None:
    """Call the diarization service to get speaker segments."""
    diarization_url = settings.diarization_service_url
    if not diarization_url:
        return None

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{diarization_url}/diarize",
            files={"file": (filename, audio_bytes)},
        )
        if resp.status_code != 200:
            logger.warning("Diarization service returned %d", resp.status_code)
            return None
        data = resp.json()
        segments = data.get("segments", [])
        logger.info("Diarization returned %d speaker turns", len(segments))
        return segments if segments else None


# ── Request schemas ──────────────────────────────────────────────────────

class AudioReadyRequest(BaseModel):
    """Sent by bot-service when audio upload is complete."""
    audio_storage_path: str = Field(..., description="Storage path for the audio file")
    user_id: uuid.UUID = Field(..., description="Owner of the meeting")


class TranscriptionCompleteRequest(BaseModel):
    """Sent by transcription worker when done."""
    segment_count: int = Field(..., ge=0, description="Number of transcript segments produced")


class SummarizationCompleteRequest(BaseModel):
    """Sent by summarization worker when done."""
    pass


class PipelineErrorRequest(BaseModel):
    """Sent by any worker on failure."""
    stage: str = Field(..., description="Pipeline stage that failed")
    error: str = Field(..., description="Human-readable error message")


# ── Pipeline trigger endpoints (called by QStash) ────────────────────────

@router.post(
    "/pipeline/transcribe/{meeting_id}",
    dependencies=[Depends(verify_qstash_signature)],
)
async def pipeline_transcribe(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """QStash-triggered: transcribe meeting audio using Groq Whisper API."""
    meeting = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting_obj = meeting.scalar_one_or_none()
    if not meeting_obj:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting_obj.audio_url:
        raise HTTPException(status_code=400, detail="Meeting has no audio file")

    try:
        # Update status
        meeting_obj.status = MeetingStatus.transcribing
        await db.flush()

        # Read audio from R2 (r2://...) or local filesystem
        from app.services import r2_storage_service

        audio_bytes = await r2_storage_service.fetch_bytes(meeting_obj.audio_url)
        filename = meeting_obj.audio_url.rstrip("/").split("/")[-1] or "audio.flac"

        # Try speaker diarization if service is available
        diarization_segments = None
        try:
            diarization_segments = await _run_diarization(audio_bytes, filename)
        except Exception as exc:
            logger.warning("Diarization unavailable, proceeding without speakers: %s", exc)

        segment_count = await transcribe_audio(
            audio_bytes, filename, meeting_id, db,
            diarization_segments=diarization_segments,
        )

        # Mark transcript ready
        meeting_obj.transcript_ready = True
        meeting_obj.status = MeetingStatus.summarizing
        await db.flush()

        # Record usage: transcription_minutes (rounded up from max segment end_time).
        # Used by quota middleware to enforce monthly plan limits.
        if meeting_obj.organization_id:
            duration_sec = (await db.execute(
                select(sa_func.coalesce(sa_func.max(TranscriptSegment.end_time), 0.0))
                .where(TranscriptSegment.meeting_id == meeting_id)
            )).scalar() or 0
            minutes = max(1, int((duration_sec + 59) // 60))
            await usage_service.record(
                db,
                organization_id=meeting_obj.organization_id,
                user_id=meeting_obj.user_id,
                meeting_id=meeting_id,
                kind=UsageKind.transcription_minutes,
                quantity=minutes,
            )

        # Generate embeddings using the meeting owner's BYOM provider so Vakta
        # (Ask) and semantic search can retrieve against this meeting. If the
        # user hasn't configured a provider — or their provider doesn't
        # support embeddings — we silently skip and FTS keeps the rest working.
        try:
            from app.models.ai_config import UserAIConfig
            from app.services.embedding_service import index_segments

            ai_config = (await db.execute(
                select(UserAIConfig)
                .where(UserAIConfig.user_id == meeting_obj.user_id)
                .where(UserAIConfig.is_active.is_(True))
                .order_by(UserAIConfig.is_default.desc(), UserAIConfig.created_at.desc())
                .limit(1)
            )).scalar_one_or_none()

            seg_rows = (await db.execute(
                select(TranscriptSegment.id, TranscriptSegment.content)
                .where(TranscriptSegment.meeting_id == meeting_id)
                .order_by(TranscriptSegment.start_time.asc())
            )).all()
            payload = [(row.id, row.content) for row in seg_rows if row.content]
            if payload and ai_config is not None:
                written = await index_segments(
                    db,
                    meeting_id=meeting_id,
                    segments=payload,
                    ai_config=ai_config,
                )
                logger.info(
                    "Embedded %d segments for meeting %s", written, meeting_id
                )
            elif ai_config is None:
                logger.info(
                    "No AI config for user %s — skipping embeddings", meeting_obj.user_id
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Embedding generation skipped for %s: %s", meeting_id, exc
            )

        # Notify via WebSocket
        pipeline = PipelineService(db)
        await pipeline._broadcast_status(
            meeting_id, "summarizing", f"Transcription complete ({segment_count} segments)"
        )

        # Queue summarization
        await publish_job(
            f"/internal/pipeline/summarize/{meeting_id}",
            {"meeting_id": str(meeting_id)},
        )

        return {"status": "ok", "segments": segment_count, "next_stage": "summarizing"}

    except Exception as exc:
        logger.exception("Transcription failed for meeting %s", meeting_id)
        meeting_obj.status = MeetingStatus.failed
        meeting_obj.error_message = f"[transcription] {exc}"
        await db.flush()

        pipeline = PipelineService(db)
        await pipeline._broadcast_status(
            meeting_id, "failed", f"Transcription failed: {exc}"
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/pipeline/summarize/{meeting_id}",
    dependencies=[Depends(verify_qstash_signature)],
)
async def pipeline_summarize(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """QStash-triggered: summarize meeting transcript using LLM."""
    meeting = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting_obj = meeting.scalar_one_or_none()
    if not meeting_obj:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        meeting_obj.status = MeetingStatus.summarizing
        await db.flush()

        await summarize_meeting(meeting_id, db)

        # Mark complete
        meeting_obj.summary_ready = True
        meeting_obj.status = MeetingStatus.completed
        await db.flush()

        # Record approximate LLM token usage. LiteLLM doesn't surface token
        # counts uniformly across providers, so we estimate from text length
        # (~4 chars per token). Accurate enough for monthly quotas.
        if meeting_obj.organization_id:
            from app.models.summary import MeetingSummary

            seg_chars = (await db.execute(
                select(sa_func.coalesce(
                    sa_func.sum(sa_func.length(TranscriptSegment.content)), 0
                )).where(TranscriptSegment.meeting_id == meeting_id)
            )).scalar() or 0

            summary_row = (await db.execute(
                select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
            )).scalar_one_or_none()
            summary_chars = len(summary_row.summary or "") if summary_row else 0

            await usage_service.record(
                db,
                organization_id=meeting_obj.organization_id,
                user_id=meeting_obj.user_id,
                meeting_id=meeting_id,
                kind=UsageKind.llm_input_tokens,
                quantity=max(1, seg_chars // 4),
            )
            await usage_service.record(
                db,
                organization_id=meeting_obj.organization_id,
                user_id=meeting_obj.user_id,
                meeting_id=meeting_id,
                kind=UsageKind.llm_output_tokens,
                quantity=max(1, summary_chars // 4),
            )

        # Run Topic Tracker against the new transcript. Records hits + emails
        # alerts to the org's configured notify_emails. Best-effort — failures
        # don't roll back the rest of the pipeline.
        try:
            from app.services import topic_tracker_service

            hits = await topic_tracker_service.scan_meeting(db, meeting_id)
            if hits:
                logger.info("Topic tracker recorded %d hits for %s", hits, meeting_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Topic tracker scan skipped for %s: %s", meeting_id, exc
            )

        # Fan out "summary ready" — Slack channel post, customer webhooks, and
        # a templated email. Each is best-effort and isolated from the others.
        if meeting_obj.organization_id:
            from app.models.summary import MeetingSummary
            from app.models.team import UserProfile
            from app.models.webhooks import WebhookEvent
            from app.services import (
                email_service,
                email_templates,
                slack_service,
                webhook_service,
            )

            summary_row = (await db.execute(
                select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
            )).scalar_one_or_none()
            summary_text = (summary_row.summary if summary_row else None) or ""
            action_items = (summary_row.action_items if summary_row else None) or []

            try:
                await slack_service.post_summary(
                    db,
                    organization_id=meeting_obj.organization_id,
                    meeting_title=meeting_obj.title,
                    meeting_id=meeting_id,
                    summary=summary_text,
                    action_items=action_items if isinstance(action_items, list) else None,
                )
            except Exception:  # noqa: BLE001
                logger.exception("Slack post failed for %s", meeting_id)

            try:
                await webhook_service.dispatch(
                    db,
                    organization_id=meeting_obj.organization_id,
                    event=WebhookEvent.summary_ready,
                    payload={
                        "meeting_id": str(meeting_id),
                        "title": meeting_obj.title,
                        "summary": summary_text[:5000],
                    },
                )
            except Exception:  # noqa: BLE001
                logger.exception("Webhook dispatch failed for %s", meeting_id)

            try:
                owner = await db.get(UserProfile, meeting_obj.user_id)
                if owner and owner.email:
                    subject, html, text = email_templates.summary_ready(
                        meeting_title=meeting_obj.title,
                        meeting_id=str(meeting_id),
                    )
                    await email_service.send_email(
                        to=owner.email, subject=subject, html=html, text=text
                    )
            except Exception:  # noqa: BLE001
                logger.exception("Summary email failed for %s", meeting_id)

        # Notify via WebSocket
        pipeline = PipelineService(db)
        await pipeline._broadcast_status(
            meeting_id, "completed", "Your meeting summary is ready!"
        )

        # Send notification
        await pipeline.notifications.create(
            user_id=meeting_obj.user_id,
            title="Meeting summary is ready!",
            body="Your meeting has been transcribed and summarized.",
            notification_type="info",
            link=f"/meetings/{meeting_id}",
        )

        return {"status": "ok", "next_stage": "done"}

    except Exception as exc:
        logger.exception("Summarization failed for meeting %s", meeting_id)
        meeting_obj.status = MeetingStatus.failed
        meeting_obj.error_message = f"[summarization] {exc}"
        await db.flush()

        pipeline = PipelineService(db)
        await pipeline._broadcast_status(
            meeting_id, "failed", f"Summarization failed: {exc}"
        )
        raise HTTPException(status_code=500, detail=str(exc))


# ── Legacy callbacks (kept for bot-service compatibility) ────────────────

@router.post(
    "/meetings/{meeting_id}/audio-ready",
    dependencies=[Depends(require_internal_auth)],
)
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

    # Queue transcription via QStash
    await publish_job(
        f"/internal/pipeline/transcribe/{meeting_id}",
        {"meeting_id": str(meeting_id)},
    )

    return {"status": "ok", "next_stage": "transcribing"}


@router.post(
    "/meetings/{meeting_id}/transcription-complete",
    dependencies=[Depends(require_internal_auth)],
)
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


@router.post(
    "/meetings/{meeting_id}/summarization-complete",
    dependencies=[Depends(require_internal_auth)],
)
async def summarization_complete(
    meeting_id: uuid.UUID,
    body: SummarizationCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Called by summarization worker when done."""
    pipeline = PipelineService(db)
    await pipeline.on_summarization_complete(meeting_id=meeting_id)
    return {"status": "ok", "next_stage": "done"}


@router.post(
    "/meetings/{meeting_id}/pipeline-error",
    dependencies=[Depends(require_internal_auth)],
)
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
