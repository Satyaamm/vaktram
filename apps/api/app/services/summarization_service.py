"""Summarization service using native provider SDKs with user's BYOM config."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.transcript import TranscriptSegment
from app.services.encryption_service import EncryptionService
from app.services.llm_service import LLMRequest, call_llm

logger = logging.getLogger(__name__)
encryption = EncryptionService()

# Prompt templates

SUMMARY_PROMPT = """You are an expert meeting summarizer. Given a meeting transcript with speaker labels and timestamps, generate a clear, concise summary.

Guidelines:
- Start with a one-sentence overview of the meeting's purpose
- Organize the summary into logical sections based on topics discussed
- Highlight key points, not every detail
- Mention participants by their speaker labels when relevant
- Keep the summary to 3-5 paragraphs maximum
- Use professional, neutral language

Format your response as plain text paragraphs."""

ACTION_ITEMS_PROMPT = """Extract action items from this meeting transcript. For each action item, provide task, assignee, deadline, and priority.

Return a JSON array:
[{"task": "...", "assignee": "...", "deadline": "...", "priority": "high|medium|low"}]

If no action items, return: []"""

DECISIONS_PROMPT = """Extract key decisions made during this meeting.

Return a JSON array:
[{"decision": "...", "context": "...", "made_by": "..."}]

If no decisions, return: []"""


async def _call_with_config(
    system_prompt: str,
    transcript: str,
    config: UserAIConfig,
    api_key: str,
) -> str:
    """Call LLM using the user's BYOM config via native provider SDK."""
    req = LLMRequest(
        provider=config.provider,
        model_name=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        extra_config=config.extra_config,
        system_prompt=system_prompt,
        user_prompt=transcript,
        temperature=0.3,
        max_tokens=2048,
    )
    return await call_llm(req)


def _parse_json_safely(text: str) -> list | dict | None:
    """Try to parse JSON from LLM output, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def _get_user_ai_config(user_id: uuid.UUID, db: AsyncSession) -> tuple[UserAIConfig, str]:
    """Get the user's default AI config. Returns (config_obj, api_key).

    Raises ValueError if no AI config is configured.
    """
    result = await db.execute(
        select(UserAIConfig).where(
            UserAIConfig.user_id == user_id,
            UserAIConfig.is_active.is_(True),
            UserAIConfig.is_default.is_(True),
        )
    )
    config = result.scalar_one_or_none()

    # If no default, try any active config
    if not config:
        result = await db.execute(
            select(UserAIConfig).where(
                UserAIConfig.user_id == user_id,
                UserAIConfig.is_active.is_(True),
            ).limit(1)
        )
        config = result.scalar_one_or_none()

    if not config:
        raise ValueError(
            "No AI model configured. Please go to Settings > AI Config to add your API key."
        )

    # Bedrock/Vertex/Ollama don't always need api_key_encrypted
    if config.provider not in ("bedrock", "vertex_ai", "ollama") and not config.api_key_encrypted:
        raise ValueError(
            "AI model configured but API key is missing. Please update your AI config."
        )

    api_key = encryption.decrypt(config.api_key_encrypted) if config.api_key_encrypted else ""

    return config, api_key


async def summarize_meeting(meeting_id: uuid.UUID, db: AsyncSession) -> None:
    """Fetch transcript segments, generate summary using user's BYOM config, and save to DB."""
    # Get meeting to find user
    meeting_result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = meeting_result.scalar_one_or_none()
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found")

    # Get user's AI config
    config, api_key = await _get_user_ai_config(meeting.user_id, db)
    logger.info(
        "Using %s/%s (provider: %s) for meeting %s",
        config.provider, config.model_name, config.provider, meeting_id,
    )

    # Get transcript segments
    result = await db.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence_number)
    )
    segments = result.scalars().all()

    if not segments:
        raise ValueError(f"No transcript segments for meeting {meeting_id}")

    # Build transcript text
    transcript_text = "\n".join(
        f"[{seg.speaker_name}] ({seg.start_time:.1f}s - {seg.end_time:.1f}s): {seg.content}"
        for seg in segments
    )

    # Run all LLM calls in parallel
    summary_text, action_items_raw, decisions_raw = await asyncio.gather(
        _call_with_config(SUMMARY_PROMPT, transcript_text, config, api_key),
        _call_with_config(ACTION_ITEMS_PROMPT, transcript_text, config, api_key),
        _call_with_config(DECISIONS_PROMPT, transcript_text, config, api_key),
    )

    action_items = _parse_json_safely(action_items_raw) or []
    decisions = _parse_json_safely(decisions_raw) or []

    model_string = f"{config.provider}/{config.model_name}"

    # Upsert summary
    existing = await db.execute(
        select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
    )
    summary = existing.scalar_one_or_none()

    if summary:
        summary.summary_text = summary_text
        summary.action_items = action_items
        summary.key_decisions = decisions
        summary.model_used = model_string
        summary.provider_used = config.provider
    else:
        summary = MeetingSummary(
            meeting_id=meeting_id,
            summary_text=summary_text,
            action_items=action_items,
            key_decisions=decisions,
            model_used=model_string,
            provider_used=config.provider,
        )
        db.add(summary)

    await db.flush()
    logger.info("Summarization complete for meeting %s using %s", meeting_id, model_string)
