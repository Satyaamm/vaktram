"""Summary generation and CRUD service."""

from __future__ import annotations

import json
import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.team import UserProfile
from app.models.transcript import TranscriptSegment
from app.services.encryption_service import EncryptionService
from app.services.llm_service import LLMRequest, call_llm

encryption = EncryptionService()

SUMMARY_PROMPT = """You are an expert meeting summarizer. Given a meeting transcript, produce a structured JSON response with:

1. "summary_text": A concise, well-structured summary (2-4 paragraphs).
2. "action_items": A list of objects with "description", "assignee" (if mentioned), and "due_date" (if mentioned).
3. "key_decisions": A list of objects with "decision" and "context".
4. "topics": A list of main topics discussed.
5. "sentiment": The overall meeting sentiment (positive, neutral, negative, mixed).

Respond ONLY with valid JSON."""


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

        # Resolve LLM config from user's BYOM settings
        config_result = await self.db.execute(
            select(UserAIConfig).where(
                UserAIConfig.user_id == user.id,
                UserAIConfig.is_active.is_(True),
                UserAIConfig.is_default.is_(True),
            )
        )
        ai_config = config_result.scalar_one_or_none()
        if not ai_config:
            # Fallback to any active config
            config_result = await self.db.execute(
                select(UserAIConfig).where(
                    UserAIConfig.user_id == user.id,
                    UserAIConfig.is_active.is_(True),
                ).limit(1)
            )
            ai_config = config_result.scalar_one_or_none()

        if not ai_config:
            raise HTTPException(
                status_code=400,
                detail="No AI model configured. Go to Settings > AI Config to add your provider.",
            )

        # Use override provider/model if provided, otherwise use config
        resolved_provider = provider or ai_config.provider
        resolved_model = model or ai_config.model_name
        api_key = encryption.decrypt(ai_config.api_key_encrypted) if ai_config.api_key_encrypted else ""

        transcript_text = "\n".join(
            f"[{s.speaker_name}] ({s.start_time:.1f}s): {s.content}" for s in segments
        )

        prompt = custom_prompt or SUMMARY_PROMPT

        req = LLMRequest(
            provider=resolved_provider,
            model_name=resolved_model,
            api_key=api_key,
            base_url=ai_config.base_url,
            extra_config=ai_config.extra_config,
            system_prompt=prompt,
            user_prompt=transcript_text,
            temperature=0.3,
            max_tokens=4096,
        )

        raw = await call_llm(req)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "summary_text": raw,
                "action_items": [],
                "key_decisions": [],
                "topics": [],
                "sentiment": "unknown",
            }

        model_string = f"{resolved_provider}/{resolved_model}"

        # Upsert summary
        existing = await self.get_summary(meeting_id, user.id)
        if existing:
            existing.summary_text = result["summary_text"]
            existing.action_items = result.get("action_items")
            existing.key_decisions = result.get("key_decisions")
            existing.topics = result.get("topics")
            existing.sentiment = result.get("sentiment")
            existing.model_used = model_string
            existing.provider_used = resolved_provider
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
            model_used=model_string,
            provider_used=resolved_provider,
        )
        self.db.add(summary)
        await self.db.flush()
        await self.db.refresh(summary)
        return summary

    async def delete_summary(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        existing = await self.get_summary(meeting_id, user_id)
        if existing is None:
            return False
        await self.db.execute(
            delete(MeetingSummary).where(MeetingSummary.id == existing.id)
        )
        return True
