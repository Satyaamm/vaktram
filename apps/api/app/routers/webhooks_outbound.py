"""CRUD for outbound webhook subscriptions.

The existing `webhooks.py` router handles inbound webhooks (Stripe, etc).
This one is for the customer's webhooks: where Vaktram POSTs events.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.models.webhooks import (
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
)
from app.services.webhook_service import generate_secret

router = APIRouter(prefix="/webhooks-out", tags=["webhooks-outbound"])


class EndpointCreate(BaseModel):
    url: HttpUrl
    events: list[str] = Field(default_factory=list)
    description: str | None = None


class EndpointRead(BaseModel):
    id: str
    url: str
    description: str | None
    events: list[str]
    is_active: bool
    secret: str | None = None  # only returned once on create


@router.get("/events")
async def list_event_types():
    """Available event types customers can subscribe to."""
    return [e.value for e in WebhookEvent]


@router.get("")
async def list_endpoints(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        return []
    rows = (await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.organization_id == user.organization_id)
        .order_by(WebhookEndpoint.created_at.desc())
    )).scalars().all()
    return [
        EndpointRead(
            id=str(ep.id),
            url=ep.url,
            description=ep.description,
            events=ep.events,
            is_active=ep.is_active,
        ).model_dump()
        for ep in rows
    ]


@router.post("", status_code=201)
async def create_endpoint(
    body: EndpointCreate,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No organization")
    valid = {e.value for e in WebhookEvent}
    bad = [e for e in body.events if e != "*" and e not in valid]
    if bad:
        raise HTTPException(400, f"Unknown event types: {bad}")
    secret = generate_secret()
    ep = WebhookEndpoint(
        organization_id=user.organization_id,
        url=str(body.url),
        events=body.events,
        description=body.description,
        secret=secret,
        is_active=True,
    )
    db.add(ep)
    await db.flush()
    return EndpointRead(
        id=str(ep.id),
        url=ep.url,
        description=ep.description,
        events=ep.events,
        is_active=ep.is_active,
        secret=secret,  # only time it's returned in plaintext
    ).model_dump()


@router.delete("/{endpoint_id}", status_code=204)
async def delete_endpoint(
    endpoint_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if not ep or ep.organization_id != user.organization_id:
        raise HTTPException(404, "Endpoint not found")
    await db.delete(ep)
    await db.flush()
    return


@router.get("/{endpoint_id}/deliveries")
async def list_deliveries(
    endpoint_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    ep = await db.get(WebhookEndpoint, endpoint_id)
    if not ep or ep.organization_id != user.organization_id:
        raise HTTPException(404, "Endpoint not found")
    rows = (await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == endpoint_id)
        .order_by(desc(WebhookDelivery.created_at))
        .limit(limit)
    )).scalars().all()
    return [
        {
            "id": str(d.id),
            "event": d.event,
            "status": d.status.value,
            "attempts": d.attempts,
            "last_status_code": d.last_status_code,
            "last_error": d.last_error,
            "next_retry_at": d.next_retry_at,
            "created_at": d.created_at,
        }
        for d in rows
    ]
