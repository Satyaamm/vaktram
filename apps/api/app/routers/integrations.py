"""Third-party integration management (Slack first, more to come)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.integrations import OrgIntegration
from app.models.team import UserProfile

router = APIRouter(prefix="/integrations", tags=["integrations"])


class SlackConfigRequest(BaseModel):
    webhook_url: HttpUrl
    channel: str | None = None


@router.get("")
async def list_integrations(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        return []
    rows = (await db.execute(
        select(OrgIntegration).where(OrgIntegration.organization_id == user.organization_id)
    )).scalars().all()
    # Never return raw config (contains webhook URL); just is_active + provider.
    return [
        {
            "provider": r.provider,
            "is_active": r.is_active,
            "channel": (r.config or {}).get("channel"),
            "configured_at": r.updated_at,
        }
        for r in rows
    ]


@router.put("/slack")
async def configure_slack(
    body: SlackConfigRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No organization")
    row = (await db.execute(
        select(OrgIntegration)
        .where(OrgIntegration.organization_id == user.organization_id)
        .where(OrgIntegration.provider == "slack")
    )).scalar_one_or_none()
    config = {"webhook_url": str(body.webhook_url), "channel": body.channel}
    if row is None:
        row = OrgIntegration(
            organization_id=user.organization_id,
            provider="slack",
            config=config,
            is_active=True,
        )
        db.add(row)
    else:
        row.config = config
        row.is_active = True
    await db.flush()
    return {"provider": "slack", "is_active": True, "channel": body.channel}


@router.delete("/slack", status_code=204)
async def disconnect_slack(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        select(OrgIntegration)
        .where(OrgIntegration.organization_id == user.organization_id)
        .where(OrgIntegration.provider == "slack")
    )).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()
    return
