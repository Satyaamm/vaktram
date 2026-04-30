"""Per-org third-party integrations (Slack incoming webhook today, more later)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrgIntegration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "org_integrations"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider", name="uq_org_provider"),
        {"schema": "vaktram"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, doc="slack | notion | linear | salesforce | hubspot")
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
