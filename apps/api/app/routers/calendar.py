"""Calendar integration endpoints — OAuth flow, sync, disconnect."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_current_user, get_db
from app.models.team import UserProfile
from app.schemas.calendar import (
    CalendarAuthorizeResponse,
    CalendarConnectionRead,
    CalendarSyncResponse,
)
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/connections", response_model=list[CalendarConnectionRead])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List all calendar connections for the authenticated user."""
    svc = CalendarService(db)
    connections = await svc.get_connections(user.id)
    return connections


@router.post("/authorize", response_model=CalendarAuthorizeResponse)
async def authorize(
    user: UserProfile = Depends(get_current_user),
):
    """Get the Google OAuth2 authorization URL."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration is not configured",
        )
    # get_authorize_url doesn't use DB, so None is safe here
    svc = CalendarService(None)  # type: ignore[arg-type]
    url = svc.get_authorize_url(user.id)
    return CalendarAuthorizeResponse(authorization_url=url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback. No auth required — state contains user_id."""
    try:
        user_id = uuid.UUID(state)
    except ValueError:
        return RedirectResponse(
            f"{settings.frontend_base_url}/settings?status=error&message=invalid_state"
        )

    try:
        svc = CalendarService(db)
        connection = await svc.handle_callback(code, user_id)
        # Trigger an immediate sync
        await svc.sync_events(user_id)
        await db.commit()
        return RedirectResponse(
            f"{settings.frontend_base_url}/settings?status=connected&provider=google"
        )
    except Exception as e:
        logger.exception("Calendar OAuth callback failed")
        await db.rollback()
        return RedirectResponse(
            f"{settings.frontend_base_url}/settings?status=error&message=oauth_failed"
        )


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendar(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Manually trigger a calendar sync."""
    svc = CalendarService(db)
    synced_count, new_titles = await svc.sync_events(user.id)
    return CalendarSyncResponse(synced_count=synced_count, new_meetings=new_titles)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Disconnect a calendar integration."""
    svc = CalendarService(db)
    deleted = await svc.disconnect(user.id, connection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Calendar connection not found")
