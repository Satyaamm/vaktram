"""TranscriptSegment model."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TranscriptSegment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transcript_segments"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaktram.meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    speaker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    speaker_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False, doc="Seconds from meeting start")
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")

    meeting: Mapped["Meeting"] = relationship(back_populates="transcript_segments")  # noqa: F821
