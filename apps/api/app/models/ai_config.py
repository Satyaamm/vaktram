"""UserAIConfig model for BYOM (Bring Your Own Model)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserAIConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_ai_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="e.g. openai, anthropic, groq, ollama"
    )
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="e.g. gpt-4o, claude-3-opus"
    )
    api_key_encrypted: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Fernet-encrypted API key"
    )
    base_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Custom base URL for self-hosted models"
    )
    extra_config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict,
        doc="Provider-specific fields: api_version, aws_region, vertex_project, etc."
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
