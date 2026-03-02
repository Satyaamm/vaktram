"""Transcript service."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.schemas.transcript import FullTranscript, TranscriptSegmentBase


class TranscriptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_meeting_access(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> Meeting:
        """Ensure the meeting exists and belongs to the user."""
        result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
        )
        meeting = result.scalar_one_or_none()
        if meeting is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting

    async def get_transcript(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> FullTranscript | None:
        await self._verify_meeting_access(meeting_id, user_id)
        result = await self.db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.sequence_number)
        )
        segments = result.scalars().all()
        if not segments:
            return None
        return FullTranscript(
            meeting_id=meeting_id,
            segments=segments,
            total_segments=len(segments),
        )

    async def bulk_create(
        self,
        meeting_id: uuid.UUID,
        segments: list[TranscriptSegmentBase],
        user_id: uuid.UUID,
    ) -> list[TranscriptSegment]:
        await self._verify_meeting_access(meeting_id, user_id)
        db_segments = []
        for seg in segments:
            db_seg = TranscriptSegment(
                meeting_id=meeting_id,
                speaker_name=seg.speaker_name,
                speaker_email=seg.speaker_email,
                content=seg.content,
                start_time=seg.start_time,
                end_time=seg.end_time,
                sequence_number=seg.sequence_number,
                confidence=seg.confidence,
                language=seg.language,
            )
            self.db.add(db_seg)
            db_segments.append(db_seg)
        await self.db.flush()
        for s in db_segments:
            await self.db.refresh(s)
        return db_segments

    async def delete_transcript(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self._verify_meeting_access(meeting_id, user_id)
        await self.db.execute(
            delete(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
        )
