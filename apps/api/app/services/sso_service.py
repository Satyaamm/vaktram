"""SSO orchestration: SAML and OIDC.

The actual SAML XML signing is delegated to onelogin/python3-saml which is
heavyweight and platform-sensitive — kept behind a try/except so dev mode
without it still imports cleanly. OIDC uses Authlib.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import SsoConnection, SsoType
from app.models.team import Organization, UserProfile

logger = logging.getLogger(__name__)


async def find_connection_by_email(
    db: AsyncSession, email: str
) -> SsoConnection | None:
    """Lookup the IdP connection for the user's email domain."""
    if "@" not in email:
        return None
    domain = email.split("@", 1)[1].lower()
    rows = await db.execute(
        select(SsoConnection)
        .where(SsoConnection.domain == domain)
        .where(SsoConnection.is_active.is_(True))
    )
    return rows.scalar_one_or_none()


def build_saml_settings(conn: SsoConnection, sp_acs_url: str, sp_entity_id: str) -> dict:
    """python3-saml settings dict for one connection."""
    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": sp_entity_id,
            "assertionConsumerService": {
                "url": sp_acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": conn.idp_entity_id or "",
            "singleSignOnService": {
                "url": conn.idp_sso_url or "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": (conn.idp_x509_cert or "").strip(),
        },
    }


async def upsert_user_from_assertion(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    email: str,
    name: str | None,
    groups: list[str] | None,
    conn: SsoConnection,
) -> UserProfile:
    """Match by email, create on first sign-in, map groups → role."""
    existing = (
        await db.execute(select(UserProfile).where(UserProfile.email == email))
    ).scalar_one_or_none()

    role = "member"
    if conn.group_role_map and groups:
        for g in groups:
            if mapped := conn.group_role_map.get(g):
                role = mapped
                break

    if existing:
        existing.organization_id = organization_id
        existing.full_name = existing.full_name or name
        existing.is_active = True
        existing.role = role
        return existing

    user = UserProfile(
        email=email,
        full_name=name,
        organization_id=organization_id,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user
