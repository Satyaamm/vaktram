"""Scheduled jobs model for APScheduler persistence."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScheduledJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks scheduled jobs (bot deployments, calendar syncs, etc.)."""

    __tablename__ = "scheduled_jobs"

    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        doc="bot_deploy | calendar_sync | pipeline_retry",
    )
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.meetings.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        doc="When the job should execute",
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        doc="When the job actually ran",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        doc="pending | running | completed | failed | cancelled",
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    retries: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
