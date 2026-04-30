"""Bot orchestration service — calls the self-hosted bot-service container."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.meeting import Meeting, MeetingStatus

settings = get_settings()


class BotService:
    """Manages meeting bot lifecycle via the self-hosted bot service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> Meeting:
        result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
        )
        meeting = result.scalar_one_or_none()
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting

    async def join_meeting(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        meeting_url_override: str | None = None,
    ) -> dict[str, Any]:
        meeting = await self._get_meeting(meeting_id, user_id)
        url = meeting_url_override or meeting.meeting_url
        if not url:
            raise HTTPException(status_code=400, detail="No meeting URL available")

        bot_url = settings.bot_service_url
        if not bot_url:
            raise HTTPException(status_code=503, detail="Bot service not configured")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{bot_url}/bots/start",
                    json={
                        "meeting_id": str(meeting_id),
                        "meeting_url": url,
                        "platform": meeting.platform.value if meeting.platform else "google_meet",
                        "bot_name": "Vaktram Notetaker",
                        "user_id": str(user_id),
                        "organization_id": str(meeting.organization_id) if meeting.organization_id else None,
                    },
                )

                if resp.status_code in (200, 201):
                    meeting.status = MeetingStatus.in_progress
                    meeting.bot_id = "active"
                    await self.db.flush()
                    return {
                        "meeting_id": meeting_id,
                        "bot_id": meeting.bot_id,
                        "status": "joining",
                        "message": "Bot is joining the meeting",
                    }
                elif resp.status_code == 409:
                    return {
                        "meeting_id": meeting_id,
                        "bot_id": meeting.bot_id,
                        "status": "already_active",
                        "message": "Bot is already in the meeting",
                    }
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Bot service error: {resp.text}",
                    )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Bot service is not reachable. Make sure it's running.",
            )

    async def leave_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        meeting = await self._get_meeting(meeting_id, user_id)

        bot_url = settings.bot_service_url
        if bot_url:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    await client.post(
                        f"{bot_url}/bots/stop",
                        json={"meeting_id": str(meeting_id)},
                    )
            except Exception:
                pass  # Bot may have already left

        meeting.status = MeetingStatus.processing
        await self.db.flush()

        return {
            "meeting_id": meeting_id,
            "bot_id": meeting.bot_id,
            "status": "left",
            "message": "Bot has left the meeting",
        }

    async def get_status(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        meeting = await self._get_meeting(meeting_id, user_id)

        # Try to get live status from bot service
        bot_url = settings.bot_service_url
        if bot_url and meeting.bot_id:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{bot_url}/bots/{meeting_id}")
                    if resp.status_code == 200:
                        data = resp.json()
                        return {
                            "meeting_id": meeting_id,
                            "bot_id": meeting.bot_id,
                            "status": data.get("status", meeting.status.value),
                            "message": f"Bot is {data.get('status', 'unknown')}",
                        }
            except Exception:
                pass

        return {
            "meeting_id": meeting_id,
            "bot_id": meeting.bot_id,
            "status": meeting.status.value,
            "message": f"Meeting is {meeting.status.value}",
        }
