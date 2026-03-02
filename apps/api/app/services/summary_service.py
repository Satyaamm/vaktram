"""Summary generation and CRUD service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.team import UserProfile
from app.models.transcript import TranscriptSegment
from app.services.llm_service import LLMService


class SummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> MeetingSummary | None:
        result = await self.db.execute(
            select(MeetingSummary)
            .join(Meeting, Meeting.id == MeetingSummary.meeting_id)
            .where(MeetingSummary.meeting_id == meeting_id, Meeting.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def generate_summary(
        self,
        meeting_id: uuid.UUID,
        user: UserProfile,
        provider: str | None = None,
        model: str | None = None,
        custom_prompt: str | None = None,
    ) -> MeetingSummary:
        # Verify meeting access
        meeting_result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user.id)
        )
        meeting = meeting_result.scalar_one_or_none()
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Fetch transcript
        seg_result = await self.db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.sequence_number)
        )
        segments = seg_result.scalars().all()
        if not segments:
            raise HTTPException(status_code=400, detail="No transcript available for this meeting")

        # Resolve LLM config
        if not provider or not model:
            config_result = await self.db.execute(
                select(UserAIConfig).where(
                    UserAIConfig.user_id == user.id, UserAIConfig.is_default.is_(True)
                )
            )
            default_config = config_result.scalar_one_or_none()
            if default_config:
                provider = provider or default_config.provider
                model = model or default_config.model_name

        llm = LLMService()
        transcript_text = "\n".join(
            f"[{s.speaker_name}] ({s.start_time:.1f}s): {s.content}" for s in segments
        )
        result = await llm.generate_summary(
            transcript=transcript_text,
            provider=provider,
            model=model,
            custom_prompt=custom_prompt,
            user=user,
        )

        # Upsert summary
        existing = await self.get_summary(meeting_id, user.id)
        if existing:
            existing.summary_text = result["summary_text"]
            existing.action_items = result.get("action_items")
            existing.key_decisions = result.get("key_decisions")
            existing.topics = result.get("topics")
            existing.sentiment = result.get("sentiment")
            existing.model_used = model
            existing.provider_used = provider
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        summary = MeetingSummary(
            meeting_id=meeting_id,
            summary_text=result["summary_text"],
            action_items=result.get("action_items"),
            key_decisions=result.get("key_decisions"),
            topics=result.get("topics"),
            sentiment=result.get("sentiment"),
            model_used=model,
            provider_used=provider,
        )
        self.db.add(summary)
        await self.db.flush()
        await self.db.refresh(summary)
        return summary

    async def delete_summary(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        # Verify ownership through join
        existing = await self.get_summary(meeting_id, user_id)
        if existing is None:
            return False
        await self.db.execute(
            delete(MeetingSummary).where(MeetingSummary.id == existing.id)
        )
        return True
