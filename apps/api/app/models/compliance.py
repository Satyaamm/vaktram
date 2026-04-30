"""Retention policies, BYOK metadata, data-export requests."""

from __future__ import annotations

import enum
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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RetentionPolicy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "retention_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    default_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    audio_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transcript_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class KmsKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-org BYOK pointer. The platform never stores the customer's key
    material — only the ARN/handle of the customer-managed key."""

    __tablename__ = "kms_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, doc="aws | gcp | azure")
    key_arn: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DataExportKind(str, enum.Enum):
    gdpr = "gdpr"
    admin = "admin"


class DataExportStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    ready = "ready"
    failed = "failed"


class DataExportRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_export_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[DataExportKind] = mapped_column(
        SAEnum(DataExportKind, name="data_export_kind", schema="vaktram"), nullable=False
    )
    status: Mapped[DataExportStatus] = mapped_column(
        SAEnum(DataExportStatus, name="data_export_status", schema="vaktram"),
        default=DataExportStatus.pending,
        nullable=False,
    )
    signed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
