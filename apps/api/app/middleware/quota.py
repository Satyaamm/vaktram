"""Quota enforcement helpers.

Use as a FastAPI dependency before any operation that consumes a metered
resource. Raises 402 when the org has exceeded its plan's monthly allowance.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.billing import Subscription, UsageKind
from app.models.team import UserProfile
from app.services import usage_service
from app.services.plans import limit_for
from sqlalchemy import select


async def _resolve_subscription(db: AsyncSession, user: UserProfile) -> Subscription:
    if not user.organization_id:
        raise HTTPException(403, "User has no organization")
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == user.organization_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        # Auto-provision a free subscription on first encounter.
        sub = Subscription(organization_id=user.organization_id)
        db.add(sub)
        await db.flush()
    return sub


def require_quota(kind: UsageKind):
    """Return a FastAPI dependency that enforces remaining quota for `kind`."""

    async def _checker(
        user: UserProfile = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        sub = await _resolve_subscription(db, user)
        allowance = limit_for(sub.plan, kind)
        if allowance == 0:  # 0 = unlimited in the plan catalog
            return
        used = await usage_service.current_period_total(
            db, organization_id=user.organization_id, kind=kind
        )
        if used >= allowance:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "quota_exceeded",
                    "kind": kind.value,
                    "used": used,
                    "limit": allowance,
                    "plan": sub.plan.value,
                },
            )

    return _checker


def require_feature(feature: str):
    """Return a dependency that 403s when the org's plan lacks `feature`."""
    from app.services.plans import has_feature

    async def _checker(
        user: UserProfile = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        sub = await _resolve_subscription(db, user)
        if not has_feature(sub.plan, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_in_plan",
                    "feature": feature,
                    "plan": sub.plan.value,
                },
            )

    return _checker
