"""Meeting and MeetingParticipant models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

import enum


class MeetingStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    processing = "processing"
    transcribing = "transcribing"
    summarizing = "summarizing"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class MeetingPlatform(str, enum.Enum):
    google_meet = "google_meet"
    zoom = "zoom"
    teams = "teams"
    zoho = "zoho"
    other = "other"


class Meeting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "meetings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.user_profiles.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.organizations.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    meeting_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[MeetingPlatform] = mapped_column(
        SAEnum(MeetingPlatform, name="meeting_platform", create_type=False, schema="vaktram"),
        nullable=False,
        default=MeetingPlatform.google_meet,
    )
    status: Mapped[MeetingStatus] = mapped_column(
        SAEnum(MeetingStatus, name="meeting_status", create_type=False, schema="vaktram"),
        nullable=False,
        default=MeetingStatus.scheduled,
    )
    scheduled_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calendar_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bot_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    auto_record: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Pipeline fields
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    participants: Mapped[list["MeetingParticipant"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    transcript_segments: Mapped[list] = relationship(
        "TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan"
    )
    summary: Mapped["MeetingSummary | None"] = relationship(
        "MeetingSummary", back_populates="meeting", cascade="all, delete-orphan", uselist=False
    )


class MeetingParticipant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "meeting_participants"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.meetings.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    speaking_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    meeting: Mapped["Meeting"] = relationship(back_populates="participants")
