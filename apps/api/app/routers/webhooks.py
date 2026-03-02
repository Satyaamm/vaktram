"""Calendar webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class GoogleCalendarWebhook(BaseModel):
    """Payload shape for Google Calendar push notifications."""
    # Google sends headers, not a JSON body, so the body may be empty.
    pass


@router.post("/google-calendar")
async def google_calendar_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_goog_channel_id: str | None = Header(None),
    x_goog_resource_id: str | None = Header(None),
    x_goog_resource_state: str | None = Header(None),
):
    """Handle Google Calendar push notification.

    Google sends event change notifications via POST with custom headers.
    """
    if x_goog_resource_state == "sync":
        # Initial sync validation -- just acknowledge
        return {"status": "sync_acknowledged"}

    if not x_goog_channel_id:
        raise HTTPException(status_code=400, detail="Missing channel ID header")

    service = CalendarService(db)
    await service.handle_google_webhook(
        channel_id=x_goog_channel_id,
        resource_id=x_goog_resource_id,
        resource_state=x_goog_resource_state,
    )
    return {"status": "processed"}


@router.post("/bot-events")
async def bot_event_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle bot status callback events (e.g. from Recall.ai)."""
    body = await request.json()
    event_type = body.get("event")
    meeting_bot_id = body.get("bot_id")

    if not event_type or not meeting_bot_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    # Route event to appropriate handler
    from app.services.bot_service import BotService

    service = BotService(db)
    await service.handle_bot_event(event_type=event_type, bot_id=meeting_bot_id, payload=body)
    return {"status": "ok"}
