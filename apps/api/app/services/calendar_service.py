"""Calendar integration service — Google Calendar OAuth & event sync."""

from __future__ import annotations

import logging
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.meeting import Meeting, MeetingPlatform, MeetingStatus
from app.models.team import CalendarConnection
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar.readonly"


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = EncryptionService()

    # ── OAuth Flow ────────────────────────────────────────────────────

    def get_authorize_url(self, user_id: uuid.UUID) -> str:
        """Build the Google OAuth2 consent URL."""
        redirect_uri = f"{settings.api_base_url}/api/v1/calendar/callback"
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": str(user_id),
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def handle_callback(self, code: str, user_id: uuid.UUID) -> CalendarConnection:
        """Exchange authorization code for tokens and store the connection."""
        redirect_uri = f"{settings.api_base_url}/api/v1/calendar/callback"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Fetch primary calendar ID
        calendar_id = await self._get_primary_calendar_id(access_token)

        # Remove existing Google connection for this user
        await self.db.execute(
            delete(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.provider == "google",
            )
        )

        connection = CalendarConnection(
            user_id=user_id,
            provider="google",
            access_token_encrypted=self.encryption.encrypt(access_token),
            refresh_token_encrypted=self.encryption.encrypt(refresh_token) if refresh_token else None,
            token_expires_at=expires_at,
            calendar_id=calendar_id,
            is_active=True,
        )
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    async def _get_primary_calendar_id(self, access_token: str) -> str:
        """Fetch the user's primary calendar ID (usually their email)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/primary",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                return resp.json().get("id", "primary")
        return "primary"

    async def _refresh_token(self, connection: CalendarConnection) -> str:
        """Refresh an expired access token. Returns the new access token."""
        refresh_token = self.encryption.decrypt(connection.refresh_token_encrypted)
        if not refresh_token:
            raise ValueError("No refresh token available")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        new_access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)

        connection.access_token_encrypted = self.encryption.encrypt(new_access_token)
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        await self.db.flush()

        return new_access_token

    async def _get_valid_token(self, connection: CalendarConnection) -> str:
        """Get a valid access token, refreshing if expired."""
        if (
            connection.token_expires_at
            and connection.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=5)
        ):
            return await self._refresh_token(connection)
        return self.encryption.decrypt(connection.access_token_encrypted) or ""

    # ── Event Sync ────────────────────────────────────────────────────

    async def sync_events(self, user_id: uuid.UUID) -> tuple[int, list[str]]:
        """Sync calendar events for a user. Returns (synced_count, new_meeting_titles)."""
        result = await self.db.execute(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.is_active.is_(True),
            )
        )
        connections = result.scalars().all()
        total_synced = 0
        new_titles: list[str] = []

        for conn in connections:
            if conn.provider == "google":
                count, titles = await self._sync_google_events(conn, user_id)
                total_synced += count
                new_titles.extend(titles)

        return total_synced, new_titles

    async def _sync_google_events(
        self, connection: CalendarConnection, user_id: uuid.UUID
    ) -> tuple[int, list[str]]:
        """Fetch upcoming events from Google Calendar and create/update meetings."""
        access_token = await self._get_valid_token(connection)
        if not access_token:
            return 0, []

        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=7)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "timeMin": now.isoformat(),
                    "timeMax": time_max.isoformat(),
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": "50",
                },
            )
            if resp.status_code != 200:
                logger.warning("Failed to fetch Google Calendar events: %s", resp.text)
                return 0, []
            data = resp.json()

        events = data.get("items", [])
        synced = 0
        new_titles: list[str] = []

        for event in events:
            meeting_url = self._extract_meeting_url(event)
            if not meeting_url:
                continue  # Skip events without video links

            meeting, is_new = await self._upsert_meeting_from_event(user_id, event, meeting_url)
            synced += 1
            if is_new:
                new_titles.append(meeting.title)

        return synced, new_titles

    def _extract_meeting_url(self, event: dict[str, Any]) -> str | None:
        """Extract a video meeting URL from a Google Calendar event."""
        # Check hangoutLink (Google Meet)
        hangout = event.get("hangoutLink")
        if hangout:
            return hangout

        # Check conferenceData for any video entry
        conf_data = event.get("conferenceData", {})
        for entry in conf_data.get("entryPoints", []):
            if entry.get("entryPointType") == "video":
                return entry.get("uri")

        # Check location/description for known meeting URLs
        for field in ("location", "description"):
            text = event.get(field, "") or ""
            for pattern in ("zoom.us/j/", "meet.google.com/", "teams.microsoft.com/"):
                if pattern in text:
                    # Extract the URL
                    for word in text.split():
                        if pattern in word and word.startswith("http"):
                            return word

        return None

    def _detect_platform(self, url: str) -> MeetingPlatform:
        """Detect the meeting platform from the URL."""
        if "meet.google.com" in url or "hangouts.google.com" in url:
            return MeetingPlatform.google_meet
        if "zoom.us" in url:
            return MeetingPlatform.zoom
        if "teams.microsoft.com" in url:
            return MeetingPlatform.teams
        return MeetingPlatform.other

    async def _upsert_meeting_from_event(
        self,
        user_id: uuid.UUID,
        event: dict[str, Any],
        meeting_url: str,
    ) -> tuple[Meeting, bool]:
        """Create or update a Meeting from a calendar event. Returns (meeting, is_new)."""
        calendar_event_id = event.get("id", "")
        result = await self.db.execute(
            select(Meeting).where(
                Meeting.user_id == user_id,
                Meeting.calendar_event_id == calendar_event_id,
            )
        )
        existing = result.scalar_one_or_none()

        # Parse event times
        start_data = event.get("start", {})
        end_data = event.get("end", {})
        scheduled_start = self._parse_event_time(start_data)
        scheduled_end = self._parse_event_time(end_data)

        if existing:
            existing.title = event.get("summary", existing.title)
            existing.meeting_url = meeting_url
            existing.platform = self._detect_platform(meeting_url)
            existing.scheduled_start = scheduled_start
            existing.scheduled_end = scheduled_end
            await self.db.flush()
            return existing, False

        meeting = Meeting(
            user_id=user_id,
            title=event.get("summary", "Untitled Meeting"),
            meeting_url=meeting_url,
            platform=self._detect_platform(meeting_url),
            status=MeetingStatus.scheduled,
            calendar_event_id=calendar_event_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            auto_record=True,
        )
        self.db.add(meeting)
        await self.db.flush()
        return meeting, True

    @staticmethod
    def _parse_event_time(time_data: dict[str, Any]) -> datetime | None:
        """Parse a Google Calendar event time (dateTime or date)."""
        dt_str = time_data.get("dateTime")
        if dt_str:
            # Handle ISO 8601 format with timezone
            return datetime.fromisoformat(dt_str)
        date_str = time_data.get("date")
        if date_str:
            return datetime.fromisoformat(date_str)
        return None

    # ── Webhook ───────────────────────────────────────────────────────

    async def handle_google_webhook(
        self,
        channel_id: str,
        resource_id: str | None,
        resource_state: str | None,
    ) -> None:
        """Process a Google Calendar push notification."""
        if resource_state == "sync":
            return  # Initial sync validation, nothing to do

        result = await self.db.execute(
            select(CalendarConnection).where(
                CalendarConnection.webhook_channel_id == channel_id,
                CalendarConnection.is_active.is_(True),
            )
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            return

        # Trigger a sync for this user
        await self.sync_events(connection.user_id)

    # ── Disconnect ────────────────────────────────────────────────────

    async def disconnect(self, user_id: uuid.UUID, connection_id: uuid.UUID) -> bool:
        """Disconnect a calendar by revoking the token and deleting the connection."""
        result = await self.db.execute(
            select(CalendarConnection).where(
                CalendarConnection.id == connection_id,
                CalendarConnection.user_id == user_id,
            )
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            return False

        # Attempt to revoke the token with Google
        access_token = self.encryption.decrypt(connection.access_token_encrypted)
        if access_token:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        GOOGLE_REVOKE_URL,
                        params={"token": access_token},
                    )
            except Exception:
                logger.warning("Failed to revoke Google token, proceeding with deletion")

        await self.db.execute(
            delete(CalendarConnection).where(CalendarConnection.id == connection_id)
        )
        return True

    # ── Queries ───────────────────────────────────────────────────────

    async def get_connections(self, user_id: uuid.UUID) -> list[CalendarConnection]:
        """Get all calendar connections for a user."""
        result = await self.db.execute(
            select(CalendarConnection).where(CalendarConnection.user_id == user_id)
        )
        return list(result.scalars().all())
