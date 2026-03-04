"""Pydantic schemas for meetings."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.meeting import MeetingPlatform, MeetingStatus


# ---- Participant ----

class ParticipantBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=50)


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantRead(ParticipantBase):
    id: uuid.UUID
    meeting_id: uuid.UUID
    speaking_duration_seconds: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ---- Meeting ----

class MeetingBase(BaseModel):
    title: str = Field(..., max_length=500)
    meeting_url: str | None = None
    platform: MeetingPlatform = MeetingPlatform.google_meet
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    auto_record: bool = True


class MeetingCreate(MeetingBase):
    participants: list[ParticipantCreate] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    meeting_url: str | None = None
    platform: MeetingPlatform | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    status: MeetingStatus | None = None
    auto_record: bool | None = None


class MeetingRead(MeetingBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    status: MeetingStatus
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    duration_seconds: int | None = None
    bot_id: str | None = None
    audio_url: str | None = None
    transcript_ready: bool = False
    summary_ready: bool = False
    created_at: datetime
    updated_at: datetime
    participants: list[ParticipantRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MeetingList(BaseModel):
    items: list[MeetingRead]
    total: int
    page: int
    page_size: int
