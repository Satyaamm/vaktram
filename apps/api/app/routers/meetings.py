"""CRUD meetings router."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_current_user, get_db
from app.models.meeting import Meeting, MeetingStatus, MeetingPlatform
from app.models.team import UserProfile
from app.schemas.meeting import MeetingCreate, MeetingList, MeetingRead, MeetingUpdate
from app.services.meeting_service import MeetingService
from app.services.queue_service import publish_job

settings = get_settings()

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


@router.get("/{meeting_id}/audio")
async def get_audio(
    meeting_id: uuid.UUID,
    request: Request,
    token: str | None = Query(None, description="JWT token for direct browser access"),
    db: AsyncSession = Depends(get_db),
):
    """Stream the audio file for a meeting. Accepts auth via header or query param."""
    from app.utils.security import decode_token

    # Try Authorization header first, then query param
    jwt_token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    elif token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(jwt_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = uuid.UUID(payload["sub"])

    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
    )
    meeting = result.scalar_one_or_none()
    if not meeting or not meeting.audio_url:
        raise HTTPException(status_code=404, detail="Audio not found")

    if not os.path.exists(meeting.audio_url):
        raise HTTPException(status_code=404, detail="Audio file missing from disk")

    return FileResponse(meeting.audio_url, media_type="audio/mpeg")


ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/flac", "audio/ogg", "audio/webm", "audio/mp4",
    "audio/m4a", "audio/x-m4a", "video/webm", "video/mp4",
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
UPLOAD_DIR = "/tmp/vaktram/uploads"


@router.post("/upload-audio", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (mp3, wav, flac, m4a, webm, mp4)"),
    title: str = Form("Uploaded Meeting"),
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Upload an audio/video file to create a meeting and kick off the transcription pipeline.

    This is the simplest way to use Vaktram — upload a recording and get
    AI-generated notes, action items, and summaries.
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Accepted: mp3, wav, flac, m4a, webm, mp4",
        )

    # Read and validate size
    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100 MB.")
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    # Save to local filesystem
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_ext = (file.filename or "audio").rsplit(".", 1)[-1] if file.filename else "bin"
    meeting_id = uuid.uuid4()
    local_path = os.path.join(UPLOAD_DIR, f"{meeting_id}.{file_ext}")

    with open(local_path, "wb") as f:
        f.write(audio_bytes)

    # Create meeting record
    meeting = Meeting(
        id=meeting_id,
        user_id=user.id,
        organization_id=user.organization_id,
        title=title,
        platform=MeetingPlatform.other,
        status=MeetingStatus.processing,
        audio_url=local_path,
    )
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)

    # Queue transcription
    queued = await publish_job(
        f"/internal/pipeline/transcribe/{meeting_id}",
        {"meeting_id": str(meeting_id)},
    )

    # If QStash isn't configured, run inline (dev mode)
    if not queued:
        import asyncio
        from app.services.transcription_service import transcribe_audio as do_transcribe
        from app.services.summarization_service import summarize_meeting as do_summarize

        try:
            # Try diarization if available
            diarization_segments = None
            try:
                from app.routers.internal import _run_diarization
                diarization_segments = await _run_diarization(audio_bytes, file.filename or "audio.wav")
            except Exception:
                pass  # Continue without diarization

            segment_count = await do_transcribe(
                audio_bytes, file.filename or "audio.wav", meeting_id, db,
                diarization_segments=diarization_segments,
            )
            meeting.transcript_ready = True
            meeting.status = MeetingStatus.summarizing
            await db.flush()

            await do_summarize(meeting_id, db)
            meeting.summary_ready = True
            meeting.status = MeetingStatus.completed
            await db.flush()
        except Exception as exc:
            meeting.status = MeetingStatus.failed
            meeting.error_message = str(exc)
            await db.flush()
            raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")

    await db.refresh(meeting, attribute_names=["participants"])
    return meeting
