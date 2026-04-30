"""Slack integration (incoming webhook).

Customers paste their Slack incoming-webhook URL into settings; we POST a
formatted message when key events fire. Incoming webhooks need no OAuth and
no scopes — simplest possible Slack onboarding.
"""

from __future__ import annotations

import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.integrations import OrgIntegration

logger = logging.getLogger(__name__)
_settings = get_settings()


async def _webhook_url(db: AsyncSession, organization_id: uuid.UUID) -> str | None:
    row = (await db.execute(
        select(OrgIntegration)
        .where(OrgIntegration.organization_id == organization_id)
        .where(OrgIntegration.provider == "slack")
        .where(OrgIntegration.is_active.is_(True))
    )).scalar_one_or_none()
    if not row:
        return None
    return (row.config or {}).get("webhook_url")


async def post_summary(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    meeting_title: str,
    meeting_id: uuid.UUID,
    summary: str | None,
    action_items: list[str] | None = None,
) -> bool:
    url = await _webhook_url(db, organization_id)
    if not url:
        return False
    base = _settings.frontend_base_url.rstrip("/")
    link = f"{base}/meetings/{meeting_id}"
    blocks: list[dict] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{link}|{meeting_title}>* — summary ready",
            },
        },
    ]
    if summary:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary[:2900]},
        })
    if action_items:
        items = "\n".join(f"• {a[:200]}" for a in action_items[:10])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Action items*\n{items}"},
        })
    return await _post(url, {"blocks": blocks})


async def post_topic_hit(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    tracker_name: str,
    meeting_title: str,
    meeting_id: uuid.UUID,
    snippet: str,
) -> bool:
    url = await _webhook_url(db, organization_id)
    if not url:
        return False
    base = _settings.frontend_base_url.rstrip("/")
    link = f"{base}/meetings/{meeting_id}"
    text = (
        f":mag: *{tracker_name}* mentioned in <{link}|{meeting_title}>\n>{snippet[:300]}"
    )
    return await _post(url, {"text": text})


async def _post(url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 300:
                logger.warning("Slack webhook returned %d: %s", resp.status_code, resp.text[:200])
                return False
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Slack webhook failed: %s", exc)
        return False
