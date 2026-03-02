"""Bot orchestration service."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.meeting import Meeting, MeetingStatus
from app.services.pipeline_service import PipelineService

settings = get_settings()


class BotService:
    """Manages meeting bot lifecycle via Recall.ai (or similar) API."""

    RECALL_BASE_URL = "https://api.recall.ai/api/v1"

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

        if not settings.recall_api_key:
            raise HTTPException(status_code=503, detail="Bot service not configured")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.RECALL_BASE_URL}/bot",
                headers={"Authorization": f"Token {settings.recall_api_key}"},
                json={
                    "meeting_url": url,
                    "bot_name": "Vaktram Notetaker",
                    "transcription_options": {"provider": "default"},
                },
                timeout=30,
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(
                    status_code=502,
                    detail=f"Bot API error: {resp.text}",
                )
            data = resp.json()

        meeting.bot_id = data.get("id")
        meeting.status = MeetingStatus.in_progress
        await self.db.flush()

        return {
            "meeting_id": meeting_id,
            "bot_id": meeting.bot_id,
            "status": "joining",
            "message": "Bot is joining the meeting",
        }

    async def leave_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        meeting = await self._get_meeting(meeting_id, user_id)
        if not meeting.bot_id:
            raise HTTPException(status_code=400, detail="No bot assigned to this meeting")

        if settings.recall_api_key:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.RECALL_BASE_URL}/bot/{meeting.bot_id}/leave",
                    headers={"Authorization": f"Token {settings.recall_api_key}"},
                    timeout=30,
                )

        meeting.status = MeetingStatus.completed
        await self.db.flush()

        return {
            "meeting_id": meeting_id,
            "bot_id": meeting.bot_id,
            "status": "left",
            "message": "Bot has left the meeting",
        }

    async def get_status(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        meeting = await self._get_meeting(meeting_id, user_id)
        return {
            "meeting_id": meeting_id,
            "bot_id": meeting.bot_id,
            "status": meeting.status.value,
            "message": f"Meeting is {meeting.status.value}",
        }

    async def handle_bot_event(self, event_type: str, bot_id: str, payload: dict[str, Any]) -> None:
        """Process a webhook event from the bot platform."""
        result = await self.db.execute(
            select(Meeting).where(Meeting.bot_id == bot_id)
        )
        meeting = result.scalar_one_or_none()
        if meeting is None:
            return  # Unknown bot -- ignore

        if event_type == "recording.done":
            # Recording finished -- kick off the processing pipeline
            audio_url = payload.get("audio_url", "")
            pipeline = PipelineService(self.db)
            await pipeline.on_audio_ready(
                meeting_id=meeting.id,
                audio_storage_path=audio_url,
                user_id=meeting.user_id,
            )
        elif event_type == "bot.leave":
            meeting.status = MeetingStatus.completed
        elif event_type == "bot.error":
            error_msg = payload.get("error", "Unknown bot error")
            pipeline = PipelineService(self.db)
            await pipeline.on_pipeline_error(
                meeting_id=meeting.id,
                stage="bot",
                error=error_msg,
            )
        elif event_type == "bot.join":
            meeting.status = MeetingStatus.in_progress

        await self.db.flush()
