"""Pydantic schemas for transcripts."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptSegmentBase(BaseModel):
    speaker_name: str = Field(..., max_length=255)
    speaker_email: str | None = Field(None, max_length=255)
    content: str
    start_time: float
    end_time: float
    sequence_number: int
    confidence: float | None = None
    language: str | None = "en"


class TranscriptSegmentCreate(TranscriptSegmentBase):
    meeting_id: uuid.UUID


class TranscriptSegmentRead(TranscriptSegmentBase):
    id: uuid.UUID
    meeting_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptBulkCreate(BaseModel):
    meeting_id: uuid.UUID
    segments: list[TranscriptSegmentBase]


class FullTranscript(BaseModel):
    meeting_id: uuid.UUID
    segments: list[TranscriptSegmentRead]
    total_segments: int
