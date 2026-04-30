"""Meeting-intel features: Ask (Vakta) chat, Topic Trackers, Soundbites, Channels.

Each model is the smallest schema that supports the user-visible feature.
Wired into the pipeline by `topic_tracker_service` (post-transcribe) and the
`/api/v1/ask`, `/api/v1/soundbites`, and `/api/v1/channels` routers.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ── Channels (shared meeting workspaces) ─────────────────────────────

class Channel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "channels"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_channel_org_slug"),
        {"schema": "vaktram"},
    )


class ChannelMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "channel_members"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), default="member", nullable=False)


class ChannelMeeting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Many-to-many: meetings can appear in multiple channels."""

    __tablename__ = "channel_meetings"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.meetings.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("channel_id", "meeting_id", name="uq_channel_meeting"),
        {"schema": "vaktram"},
    )


# ── Topic Tracker (keyword alerts across all calls) ─────────────────

class TopicTracker(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-org tracker. The `keywords` array is matched (case-insensitive)
    against new transcript segments at the end of the pipeline."""

    __tablename__ = "topic_trackers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_emails: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )


class TopicHit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific transcript segment that matched a tracker."""

    __tablename__ = "topic_hits"

    tracker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.topic_trackers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.transcript_segments.id", ondelete="CASCADE"),
        nullable=True,
    )
    matched_keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)


# ── Soundbites (clip + share short audio segments) ───────────────────

class Soundbite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "soundbites"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Ask (Vakta — chat with your meetings) ───────────────────────────

class AskScope(str, enum.Enum):
    """RAG retrieval scope for an ask thread."""
    meeting = "meeting"     # one meeting
    channel = "channel"     # all meetings in a channel
    organization = "organization"  # everything the user can see


class AskThread(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ask_threads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope: Mapped[AskScope] = mapped_column(
        SAEnum(AskScope, name="ask_scope", schema="vaktram"),
        nullable=False,
        default=AskScope.organization,
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, doc="meeting/channel id when scope!=organization"
    )

    messages: Mapped[list["AskMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class AskMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ask_messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.ask_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, doc="user | assistant")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict] | None] = mapped_column(
        JSONB, nullable=True,
        doc="[{meeting_id, segment_id, content, score}, ...]",
    )

    thread: Mapped[AskThread] = relationship(back_populates="messages")
