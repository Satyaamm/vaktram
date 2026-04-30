"""Outbound webhook delivery.

Each call to ``dispatch(db, event, payload, organization_id)``:
  1. Looks up active endpoints for the org subscribed to ``event``.
  2. For each endpoint, persists a WebhookDelivery row and POSTs the payload
     with an HMAC-SHA256 signature in ``X-Vaktram-Signature``.
  3. On non-2xx, marks the row failed and schedules a retry (exponential
     backoff up to 6 attempts, then dead).

The retry loop runs as a background task triggered by the scheduler — this
file only does the initial delivery + state recording.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhooks import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
)

logger = logging.getLogger(__name__)
SIG_HEADER = "X-Vaktram-Signature"
EVENT_HEADER = "X-Vaktram-Event"
USER_AGENT = "Vaktram-Webhooks/1.0"
TIMEOUT_S = 10
MAX_ATTEMPTS = 6


def generate_secret() -> str:
    """A new HMAC secret. Show once on creation; we store the raw value."""
    return f"whsec_{secrets.token_urlsafe(32)}"


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def dispatch(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    event: WebhookEvent | str,
    payload: dict[str, Any],
) -> int:
    """Send `event` to every active endpoint subscribed to it.

    Returns count of endpoints attempted. Caller commits.
    """
    event_name = event.value if isinstance(event, WebhookEvent) else str(event)
    rows = (
        await db.execute(
            select(WebhookEndpoint)
            .where(WebhookEndpoint.organization_id == organization_id)
            .where(WebhookEndpoint.is_active.is_(True))
        )
    ).scalars().all()

    targets = [
        ep for ep in rows
        if not ep.events or event_name in ep.events or "*" in ep.events
    ]

    body_json = json.dumps(
        {"event": event_name, "data": payload, "ts": datetime.now(timezone.utc).isoformat()},
        default=str,
    ).encode()

    n = 0
    for ep in targets:
        delivery = WebhookDelivery(
            endpoint_id=ep.id,
            event=event_name,
            payload=payload,
            status=DeliveryStatus.pending,
            attempts=0,
        )
        db.add(delivery)
        await db.flush()

        await _attempt(db, ep, delivery, body_json)
        n += 1

    return n


async def _attempt(
    db: AsyncSession,
    ep: WebhookEndpoint,
    delivery: WebhookDelivery,
    body: bytes,
) -> None:
    delivery.attempts += 1
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        SIG_HEADER: sign(ep.secret, body),
        EVENT_HEADER: delivery.event,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            resp = await client.post(ep.url, content=body, headers=headers)
        delivery.last_status_code = resp.status_code
        if 200 <= resp.status_code < 300:
            delivery.status = DeliveryStatus.succeeded
            delivery.next_retry_at = None
            return
        delivery.last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:  # noqa: BLE001
        delivery.last_error = str(exc)[:500]

    if delivery.attempts >= MAX_ATTEMPTS:
        delivery.status = DeliveryStatus.dead
        delivery.next_retry_at = None
        logger.error(
            "Webhook DEAD: endpoint=%s event=%s err=%s",
            ep.id, delivery.event, delivery.last_error,
        )
    else:
        # Exponential backoff: 1m, 4m, 16m, 1h, 4h, dead
        delay_min = 4 ** (delivery.attempts - 1)
        delivery.status = DeliveryStatus.failed
        delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=delay_min)


async def process_retries(db: AsyncSession, batch_size: int = 50) -> int:
    """Reattempt deliveries whose next_retry_at has passed.

    Called by the scheduler every minute. Returns number processed.
    """
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.status == DeliveryStatus.failed)
            .where(WebhookDelivery.next_retry_at.isnot(None))
            .where(WebhookDelivery.next_retry_at <= now)
            .limit(batch_size)
        )
    ).scalars().all()

    processed = 0
    for delivery in rows:
        ep = await db.get(WebhookEndpoint, delivery.endpoint_id)
        if not ep or not ep.is_active:
            delivery.status = DeliveryStatus.dead
            continue
        body = json.dumps(
            {"event": delivery.event, "data": delivery.payload, "retry": True},
            default=str,
        ).encode()
        await _attempt(db, ep, delivery, body)
        processed += 1
    return processed
