"""Pipeline orchestration -- connects bot -> transcription -> summarization -> notification."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting, MeetingStatus
from app.services.notification_service import NotificationService
from app.routers.ws import manager as ws_manager

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrates the meeting processing pipeline stages."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notifications = NotificationService(db)

    async def _get_meeting(self, meeting_id: uuid.UUID) -> Meeting | None:
        result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def _broadcast_status(
        self, meeting_id: uuid.UUID, status: str, message: str
    ) -> None:
        """Broadcast a pipeline status update over the WebSocket."""
        await ws_manager.broadcast(
            str(meeting_id),
            {
                "type": "pipeline_status",
                "meeting_id": str(meeting_id),
                "status": status,
                "message": message,
            },
        )

    # ── Stage callbacks ──────────────────────────────────────────────────

    async def on_audio_ready(
        self,
        meeting_id: uuid.UUID,
        audio_storage_path: str,
        user_id: uuid.UUID,
    ) -> None:
        """Called when the bot finishes recording and audio is uploaded to storage."""
        meeting = await self._get_meeting(meeting_id)
        if meeting is None:
            logger.warning("on_audio_ready: meeting %s not found", meeting_id)
            return

        meeting.status = MeetingStatus.transcribing
        meeting.audio_url = audio_storage_path
        await self.db.flush()

        await self.notifications.create(
            user_id=user_id,
            title="Recording complete",
            body="Your meeting recording is ready. Transcription is starting.",
            notification_type="info",
            link=f"/meetings/{meeting_id}",
        )

        await self._broadcast_status(
            meeting_id, "transcribing", "Recording complete, transcription starting"
        )

        logger.info(
            "Pipeline: meeting %s audio ready, status -> transcribing", meeting_id
        )

    async def on_transcription_complete(
        self, meeting_id: uuid.UUID, segment_count: int
    ) -> None:
        """Called when the transcription worker finishes."""
        meeting = await self._get_meeting(meeting_id)
        if meeting is None:
            logger.warning("on_transcription_complete: meeting %s not found", meeting_id)
            return

        meeting.transcript_ready = True
        meeting.status = MeetingStatus.summarizing
        await self.db.flush()

        await self.notifications.create(
            user_id=meeting.user_id,
            title="Transcription complete",
            body=f"Transcription complete ({segment_count} segments). Generating summary.",
            notification_type="info",
            link=f"/meetings/{meeting_id}",
        )

        await self._broadcast_status(
            meeting_id, "summarizing", "Transcription complete, generating summary"
        )

        logger.info(
            "Pipeline: meeting %s transcription done (%d segments), status -> summarizing",
            meeting_id,
            segment_count,
        )

    async def on_summarization_complete(self, meeting_id: uuid.UUID) -> None:
        """Called when the summarization worker finishes."""
        meeting = await self._get_meeting(meeting_id)
        if meeting is None:
            logger.warning(
                "on_summarization_complete: meeting %s not found", meeting_id
            )
            return

        meeting.summary_ready = True
        meeting.status = MeetingStatus.completed
        await self.db.flush()

        await self.notifications.create(
            user_id=meeting.user_id,
            title="Meeting summary is ready!",
            body="Your meeting summary has been generated and is ready to view.",
            notification_type="info",
            link=f"/meetings/{meeting_id}",
        )

        await self._broadcast_status(
            meeting_id, "completed", "Your meeting summary is ready!"
        )

        logger.info("Pipeline: meeting %s completed", meeting_id)

    async def on_pipeline_error(
        self, meeting_id: uuid.UUID, stage: str, error: str
    ) -> None:
        """Called when any pipeline stage fails."""
        meeting = await self._get_meeting(meeting_id)
        if meeting is None:
            logger.warning("on_pipeline_error: meeting %s not found", meeting_id)
            return

        meeting.status = MeetingStatus.failed
        meeting.error_message = f"[{stage}] {error}"
        await self.db.flush()

        await self.notifications.create(
            user_id=meeting.user_id,
            title="Processing failed",
            body=f"An error occurred during {stage}: {error}",
            notification_type="error",
            link=f"/meetings/{meeting_id}",
        )

        await self._broadcast_status(
            meeting_id, "failed", f"Processing failed at {stage}: {error}"
        )

        logger.error(
            "Pipeline: meeting %s failed at stage %s: %s",
            meeting_id,
            stage,
            error,
        )
