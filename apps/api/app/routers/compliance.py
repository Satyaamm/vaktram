"""Compliance APIs: retention policy, audit log, BYOK, data export (GDPR)."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.compliance import (
    DataExportKind,
    DataExportRequest,
    DataExportStatus,
    KmsKey,
    RetentionPolicy,
)
from app.models.team import AuditLog, UserProfile
from app.security.permissions import (
    P_AUDIT_READ,
    P_TEAM_MANAGE,
    require_permission,
)
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])


# ── Retention ──────────────────────────────────────────────────────────

@router.get("/retention")
async def get_retention(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No org")
    policy = (
        await db.execute(
            select(RetentionPolicy).where(RetentionPolicy.organization_id == user.organization_id)
        )
    ).scalar_one_or_none()
    return policy or {"default_days": 365, "legal_hold": False}


@router.put("/retention", dependencies=[Depends(require_permission(P_TEAM_MANAGE))])
async def set_retention(
    body: dict,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No org")
    policy = (
        await db.execute(
            select(RetentionPolicy).where(RetentionPolicy.organization_id == user.organization_id)
        )
    ).scalar_one_or_none()
    if policy is None:
        policy = RetentionPolicy(organization_id=user.organization_id)
        db.add(policy)
    policy.default_days = int(body.get("default_days", policy.default_days))
    policy.audio_days = body.get("audio_days")
    policy.transcript_days = body.get("transcript_days")
    policy.summary_days = body.get("summary_days")
    policy.legal_hold = bool(body.get("legal_hold", policy.legal_hold))
    await db.flush()
    return policy


# ── Audit log ──────────────────────────────────────────────────────────

@router.get("/audit", dependencies=[Depends(require_permission(P_AUDIT_READ))])
async def list_audit(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    after: str | None = None,
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id) if r.user_id else None,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "ip": r.ip_address,
            "ts": r.created_at.isoformat(),
            "details": {k: v for k, v in (r.details or {}).items() if k not in ("row_hash", "prev_hash")},
        }
        for r in rows
    ]


@router.get("/audit/verify", dependencies=[Depends(require_permission(P_AUDIT_READ))])
async def verify_audit_chain(db: AsyncSession = Depends(get_db)):
    return await audit_service.verify_chain(db)


# ── BYOK ──────────────────────────────────────────────────────────────

@router.put("/byok", dependencies=[Depends(require_permission(P_TEAM_MANAGE))])
async def configure_byok(
    body: dict,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No org")
    provider = body.get("provider")
    arn = body.get("key_arn")
    if provider not in ("aws", "gcp", "azure") or not arn:
        raise HTTPException(400, "provider and key_arn required")
    key = (
        await db.execute(
            select(KmsKey).where(KmsKey.organization_id == user.organization_id)
        )
    ).scalar_one_or_none()
    if key is None:
        key = KmsKey(organization_id=user.organization_id, provider=provider, key_arn=arn)
        db.add(key)
    else:
        key.provider = provider
        key.key_arn = arn
        key.enabled = True
    await db.flush()
    return {"provider": key.provider, "key_arn": key.key_arn, "enabled": key.enabled}


# ── Data export (GDPR) ────────────────────────────────────────────────

@router.post("/export")
async def request_export(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No org")
    req = DataExportRequest(
        organization_id=user.organization_id,
        user_id=user.id,
        kind=DataExportKind.gdpr,
        status=DataExportStatus.pending,
    )
    db.add(req)
    await db.flush()
    # Real impl: enqueue a job that builds a signed-URL zip and emails the user.
    return {"id": str(req.id), "status": req.status.value}


@router.delete("/me", status_code=204)
async def gdpr_erase(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR right-to-erasure for the calling user.

    Soft-deletes by deactivating + scrubbing PII. We retain audit rows by spec
    obligation; the user reference becomes anonymous via ondelete=SET NULL.
    """
    user.is_active = False
    user.email = f"deleted-{user.id}@example.invalid"
    user.full_name = None
    user.avatar_url = None
    user.password_hash = None
    await db.flush()
    return
