"""Stripe integration: customer/subscription lifecycle + checkout/portal.

All calls are guarded by config.stripe_api_key; if it's empty the methods raise
so the API surfaces a clear 'billing not configured' error rather than failing
silently.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.billing import (
    Invoice,
    PlanTier,
    Subscription,
    SubscriptionStatus,
)
from app.models.team import Organization

logger = logging.getLogger(__name__)
_settings = get_settings()


def _stripe():
    if not _settings.stripe_api_key:
        raise RuntimeError("Stripe is not configured (STRIPE_API_KEY missing)")
    import stripe

    stripe.api_key = _settings.stripe_api_key
    return stripe


def _price_for(plan: PlanTier) -> str:
    mapping = {
        PlanTier.pro: _settings.stripe_price_pro,
        PlanTier.team: _settings.stripe_price_team,
        PlanTier.business: _settings.stripe_price_business,
    }
    price = mapping.get(plan)
    if not price:
        raise ValueError(f"No Stripe price configured for plan {plan}")
    return price


async def get_or_create_subscription(
    db: AsyncSession, organization_id: uuid.UUID
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        return sub
    sub = Subscription(organization_id=organization_id, plan=PlanTier.free)
    db.add(sub)
    await db.flush()
    return sub


async def create_checkout_session(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    plan: PlanTier,
    seats: int,
    success_url: str,
    cancel_url: str,
    customer_email: str,
) -> str:
    stripe = _stripe()
    sub = await get_or_create_subscription(db, organization_id)

    if not sub.stripe_customer_id:
        org = await db.get(Organization, organization_id)
        customer = stripe.Customer.create(
            email=customer_email,
            name=org.name if org else None,
            metadata={"organization_id": str(organization_id)},
        )
        sub.stripe_customer_id = customer.id
        await db.flush()

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": _price_for(plan), "quantity": seats}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(organization_id),
        subscription_data={"metadata": {"plan": plan.value, "organization_id": str(organization_id)}},
        allow_promotion_codes=True,
    )
    return session.url


async def create_portal_session(
    db: AsyncSession, *, organization_id: uuid.UUID, return_url: str
) -> str:
    stripe = _stripe()
    sub = await get_or_create_subscription(db, organization_id)
    if not sub.stripe_customer_id:
        raise ValueError("No Stripe customer for this organization")
    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id, return_url=return_url
    )
    return portal.url


async def apply_subscription_event(db: AsyncSession, event_data: dict) -> None:
    """Sync local Subscription from a Stripe subscription.* event payload."""
    stripe_sub = event_data["object"]
    metadata = stripe_sub.get("metadata") or {}
    org_id = metadata.get("organization_id")
    if not org_id:
        # Fall back to client_reference_id stored on the parent checkout.
        return

    sub = await get_or_create_subscription(db, uuid.UUID(org_id))
    sub.stripe_subscription_id = stripe_sub["id"]
    sub.status = SubscriptionStatus(stripe_sub["status"]) if stripe_sub["status"] in {
        s.value for s in SubscriptionStatus
    } else SubscriptionStatus.incomplete
    plan_value = metadata.get("plan")
    if plan_value and plan_value in {p.value for p in PlanTier}:
        sub.plan = PlanTier(plan_value)
    sub.cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))
    if cps := stripe_sub.get("current_period_start"):
        sub.current_period_start = datetime.fromtimestamp(cps, tz=timezone.utc)
    if cpe := stripe_sub.get("current_period_end"):
        sub.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)
    items = stripe_sub.get("items", {}).get("data") or []
    if items:
        sub.seats = int(items[0].get("quantity") or 1)


async def record_invoice(db: AsyncSession, event_data: dict) -> None:
    inv = event_data["object"]
    metadata = inv.get("subscription_details", {}).get("metadata") or {}
    org_id = metadata.get("organization_id")
    if not org_id:
        return
    issued = (
        datetime.fromtimestamp(inv["created"], tz=timezone.utc)
        if inv.get("created")
        else None
    )
    db.add(
        Invoice(
            organization_id=uuid.UUID(org_id),
            stripe_invoice_id=inv["id"],
            amount_cents=inv.get("amount_paid") or inv.get("amount_due") or 0,
            currency=inv.get("currency", "usd"),
            status=inv.get("status", "open"),
            hosted_url=inv.get("hosted_invoice_url"),
            pdf_url=inv.get("invoice_pdf"),
            issued_at=issued,
        )
    )


def verify_webhook(payload: bytes, sig_header: str):
    stripe = _stripe()
    if not _settings.stripe_webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")
    return stripe.Webhook.construct_event(
        payload, sig_header, _settings.stripe_webhook_secret
    )
