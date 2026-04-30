"""SSO connections, SCIM tokens, and RBAC roles."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SsoType(str, enum.Enum):
    saml = "saml"
    oidc = "oidc"


class SsoConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sso_connections"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[SsoType] = mapped_column(
        SAEnum(SsoType, name="sso_type", schema="vaktram"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # SAML
    idp_metadata_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    idp_entity_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idp_sso_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idp_x509_cert: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OIDC
    oidc_issuer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    oidc_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    oidc_client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Attribute mapping (JSON: maps IdP claim names to local fields)
    attribute_map: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Group → role mapping
    group_role_map: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ScimToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scim_tokens"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    token_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoleScope(str, enum.Enum):
    organization = "organization"
    team = "team"
    meeting = "meeting"


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_role_org_name"),
        {"schema": "vaktram"},
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RoleAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "role_assignments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaktram.roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope: Mapped[RoleScope] = mapped_column(
        SAEnum(RoleScope, name="role_scope", schema="vaktram"), nullable=False
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, doc="org/team/meeting id depending on scope"
    )
