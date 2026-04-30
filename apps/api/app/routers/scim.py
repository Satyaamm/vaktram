"""SCIM 2.0 endpoints for IdP-driven user provisioning.

Spec: RFC 7643 (schemas) + RFC 7644 (protocol). We implement the common
subset: Users + Groups CRUD, ListResponse, basic filter.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.identity import ScimToken
from app.models.team import UserProfile

router = APIRouter(prefix="/scim/v2", tags=["scim"])


async def _verify_scim(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """Authenticate a SCIM bearer token and return its organization_id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing SCIM bearer token")
    raw = authorization.split(" ", 1)[1]
    digest = hashlib.sha256(raw.encode()).hexdigest()
    rows = await db.execute(select(ScimToken).where(ScimToken.token_hash == digest))
    token = rows.scalar_one_or_none()
    if not token:
        raise HTTPException(401, "Invalid SCIM token")
    return token.organization_id


def _scim_user(u: UserProfile) -> dict:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": str(u.id),
        "userName": u.email,
        "name": {"formatted": u.full_name or ""},
        "emails": [{"value": u.email, "primary": True}],
        "active": u.is_active,
        "meta": {"resourceType": "User"},
    }


@router.get("/Users")
async def list_users(
    org_id: uuid.UUID = Depends(_verify_scim),
    db: AsyncSession = Depends(get_db),
    startIndex: int = 1,
    count: int = 100,
    filter: str | None = None,
):
    stmt = select(UserProfile).where(UserProfile.organization_id == org_id)
    if filter and filter.startswith("userName eq "):
        email = filter.split("userName eq ", 1)[1].strip().strip('"')
        stmt = stmt.where(UserProfile.email == email)
    rows = (await db.execute(stmt.offset(startIndex - 1).limit(count))).scalars().all()
    total = (
        await db.execute(
            select(UserProfile).where(UserProfile.organization_id == org_id)
        )
    ).scalars().all()
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(total),
        "startIndex": startIndex,
        "itemsPerPage": len(rows),
        "Resources": [_scim_user(u) for u in rows],
    }


@router.post("/Users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: dict,
    org_id: uuid.UUID = Depends(_verify_scim),
    db: AsyncSession = Depends(get_db),
):
    email = body.get("userName")
    if not email:
        raise HTTPException(400, "userName required")
    existing = (
        await db.execute(select(UserProfile).where(UserProfile.email == email))
    ).scalar_one_or_none()
    if existing:
        existing.organization_id = org_id
        existing.is_active = body.get("active", True)
        existing.full_name = (body.get("name") or {}).get("formatted") or existing.full_name
        await db.flush()
        return _scim_user(existing)
    user = UserProfile(
        email=email,
        full_name=(body.get("name") or {}).get("formatted"),
        organization_id=org_id,
        is_active=body.get("active", True),
        role="member",
    )
    db.add(user)
    await db.flush()
    return _scim_user(user)


@router.patch("/Users/{user_id}")
async def patch_user(
    user_id: uuid.UUID,
    body: dict,
    org_id: uuid.UUID = Depends(_verify_scim),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(UserProfile, user_id)
    if not user or user.organization_id != org_id:
        raise HTTPException(404, "User not found")
    for op in body.get("Operations", []):
        path = op.get("path")
        value = op.get("value")
        if path == "active":
            user.is_active = bool(value)
        elif path == "userName":
            user.email = value
        elif path == "name.formatted":
            user.full_name = value
    await db.flush()
    return _scim_user(user)


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deprovision_user(
    user_id: uuid.UUID,
    org_id: uuid.UUID = Depends(_verify_scim),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(UserProfile, user_id)
    if not user or user.organization_id != org_id:
        raise HTTPException(404, "User not found")
    user.is_active = False
    await db.flush()
    return


def issue_scim_token(plain: str) -> tuple[str, str]:
    """Return (prefix, sha256_hex) for storage. Only the plain token is shown once."""
    return plain[:8], hashlib.sha256(plain.encode()).hexdigest()


def generate_token() -> str:
    return f"scim_{secrets.token_urlsafe(32)}"
