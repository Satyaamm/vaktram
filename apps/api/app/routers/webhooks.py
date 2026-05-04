"""Calendar webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.calendar_service import CalendarService
from app.utils.internal_auth import require_internal_auth

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


@router.post("/bot-events", dependencies=[Depends(require_internal_auth)])
async def bot_event_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle bot status callback events from the self-hosted bot service.

    Authenticated by the shared bot secret — only the bot service (or a
    worker that knows BOT_SHARED_SECRET) can drive meeting state."""
    body = await request.json()
    event_type = body.get("event")
    meeting_id = body.get("meeting_id")

    if not event_type or not meeting_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    import uuid
    from app.models.meeting import Meeting, MeetingStatus
    from sqlalchemy import select

    mid = uuid.UUID(meeting_id)
    result = await db.execute(select(Meeting).where(Meeting.id == mid))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if event_type == "bot_joined":
        meeting.status = MeetingStatus.in_progress
        meeting.bot_id = "active"
    elif event_type == "bot_left":
        meeting.status = MeetingStatus.processing
    elif event_type == "bot_error":
        meeting.status = MeetingStatus.failed
        meeting.error_message = body.get("error", "Bot error")
    await db.flush()

    return {"status": "ok"}
