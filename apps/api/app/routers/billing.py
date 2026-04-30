"""Billing endpoints: plans catalog, subscription, checkout, portal, webhook."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.billing import Subscription, UsageKind
from app.models.team import UserProfile
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalRequest,
    PortalResponse,
    SubscriptionRead,
    UsageSummary,
    UsageSummaryEntry,
)
from app.services import billing_service, usage_service
from app.services.plans import PLANS, limit_for

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans")
async def list_plans():
    return {
        tier.value: {
            "name": p.name,
            "monthly_price_cents": p.monthly_price_cents,
            "seat_limit": p.seat_limit,
            "features": sorted(p.features),
            "limits": {k.value: v for k, v in p.limits.items()},
        }
        for tier, p in PLANS.items()
    }


@router.get("/subscription", response_model=SubscriptionRead)
async def get_subscription(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "User has no organization")
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == user.organization_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = Subscription(organization_id=user.organization_id)
        db.add(sub)
        await db.flush()
    return sub


@router.get("/usage", response_model=UsageSummary)
async def get_usage(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "User has no organization")
    sub = (
        await db.execute(
            select(Subscription).where(Subscription.organization_id == user.organization_id)
        )
    ).scalar_one_or_none()
    plan = sub.plan if sub else None
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    entries: list[UsageSummaryEntry] = []
    for kind in UsageKind:
        used = await usage_service.current_period_total(
            db, organization_id=user.organization_id, kind=kind, period_start=period_start
        )
        cap = limit_for(plan, kind) if plan else 0
        entries.append(
            UsageSummaryEntry(
                kind=kind,
                used=used,
                limit=cap,
                remaining=-1 if cap == 0 else max(0, cap - used),
            )
        )
    return UsageSummary(plan=plan or "free", period_start=period_start, entries=entries)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "User has no organization")
    if user.role not in ("admin", "owner"):
        raise HTTPException(403, "Only admins can manage billing")
    try:
        url = await billing_service.create_checkout_session(
            db,
            organization_id=user.organization_id,
            plan=body.plan,
            seats=body.seats,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            customer_email=user.email,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return CheckoutResponse(url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    body: PortalRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id or user.role not in ("admin", "owner"):
        raise HTTPException(403, "Only admins can manage billing")
    try:
        url = await billing_service.create_portal_session(
            db, organization_id=user.organization_id, return_url=body.return_url
        )
    except (RuntimeError, ValueError) as e:
        raise HTTPException(503, str(e))
    return PortalResponse(url=url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Stripe → us. Verifies HMAC and dispatches to the relevant handler."""
    if not stripe_signature:
        raise HTTPException(400, "Missing Stripe-Signature header")
    payload = await request.body()
    try:
        event = billing_service.verify_webhook(payload, stripe_signature)
    except Exception as e:  # noqa: BLE001
        logger.warning("Stripe webhook signature failed: %s", e)
        raise HTTPException(400, "Invalid signature")

    et = event["type"]
    data = event["data"]
    if et.startswith("customer.subscription."):
        await billing_service.apply_subscription_event(db, data)
    elif et in ("invoice.paid", "invoice.payment_failed", "invoice.finalized"):
        await billing_service.record_invoice(db, data)
    else:
        logger.debug("Unhandled Stripe event: %s", et)
    return {"received": True}
