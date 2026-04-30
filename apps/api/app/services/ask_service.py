"""Vakta — Vaktram's RAG assistant over a user's meetings.

Pure BYOM: every retrieval embedding and every chat completion uses the
user's own provider/key from `UserAIConfig`. If the user hasn't configured
one, we raise a clear error that the router converts into a 412 Precondition
Failed so the UI can prompt them to set up an AI provider.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import UserAIConfig
from app.models.intel import AskMessage, AskScope, AskThread
from app.models.meeting import Meeting
from app.services.encryption_service import EncryptionService
from app.services.llm_service import LLMRequest, call_llm
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)
_enc = EncryptionService()
TOP_K = 6


class NoAIConfigError(RuntimeError):
    """Raised when a user calls Vakta without a configured AI provider."""


@dataclass
class Citation:
    meeting_id: str
    segment_id: str | None
    meeting_title: str | None
    content: str
    speaker_name: str | None
    start_time: float | None
    score: float


SYSTEM_PROMPT = """You are Vakta, Vaktram's meeting assistant. Answer the user's
questions about their meetings, ALWAYS grounded in the provided context. If
the context doesn't contain enough information, say so and suggest which
meetings might be relevant.

When you reference specific information, cite it inline as [^1], [^2] etc.,
matching the order of the supplied snippets. Keep answers concise.
"""


def _build_user_prompt(
    citations: list[Citation],
    history: list[AskMessage],
    question: str,
) -> str:
    """Fold context + chat history + new question into one string.

    `LLMRequest` accepts a single `user_prompt`, so we hand-build a
    role-tagged transcript that any provider can consume.
    """
    blocks = []
    if citations:
        ctx = []
        for i, c in enumerate(citations, start=1):
            speaker = c.speaker_name or "Unknown"
            ts = f" @{c.start_time:.0f}s" if c.start_time is not None else ""
            ctx.append(
                f"[^{i}] Meeting: {c.meeting_title or c.meeting_id}{ts}\n"
                f"   {speaker}: {c.content}"
            )
        blocks.append("Relevant meeting snippets:\n" + "\n\n".join(ctx))
    else:
        blocks.append(
            "Relevant meeting snippets:\n(no relevant meeting context found)"
        )

    if history:
        chat = []
        for m in history:
            label = "User" if m.role == "user" else "Assistant"
            chat.append(f"{label}: {m.content}")
        blocks.append("Previous turns:\n" + "\n".join(chat))

    blocks.append(f"User: {question}\nAssistant:")
    return "\n\n".join(blocks)


async def answer(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    thread: AskThread,
    question: str,
) -> AskMessage:
    """Run one Q&A turn — retrieves, calls LLM, persists user+assistant
    turns. Raises NoAIConfigError if the user has no AI provider set up."""

    config = await _load_ai_config(db, user_id)
    if config is None:
        raise NoAIConfigError(
            "Configure an AI provider in Settings → AI Config to use Vakta."
        )
    api_key = _decrypt_key(config)

    # 1) Persist the user turn first.
    user_turn = AskMessage(thread_id=thread.id, role="user", content=question)
    db.add(user_turn)
    await db.flush()

    # 2) Retrieve top-K snippets via hybrid search, scoped to the thread.
    citations = await _retrieve(
        db,
        user_id=user_id,
        organization_id=organization_id,
        thread=thread,
        query=question,
        ai_config=config,
    )

    # 3) Build prompt + call the user's BYOM LLM.
    history = (await db.execute(
        select(AskMessage)
        .where(AskMessage.thread_id == thread.id)
        .order_by(AskMessage.created_at.asc())
    )).scalars().all()
    # Drop the just-added question so it isn't duplicated in history.
    history = [m for m in history if m.id != user_turn.id]

    answer_text = await call_llm(LLMRequest(
        provider=config.provider,
        model_name=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        extra_config=config.extra_config,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_user_prompt(citations, history, question),
        temperature=0.3,
        max_tokens=1500,
    ))

    # 4) Persist the assistant turn with citations.
    assistant_turn = AskMessage(
        thread_id=thread.id,
        role="assistant",
        content=answer_text,
        citations=[c.__dict__ for c in citations],
    )
    db.add(assistant_turn)
    await db.flush()
    return assistant_turn


# ── helpers ──────────────────────────────────────────────────────────

async def _retrieve(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    thread: AskThread,
    query: str,
    ai_config: UserAIConfig,
) -> list[Citation]:
    search = SearchService(db)
    hits = await search.search(
        query=query,
        user_id=user_id,
        organization_id=organization_id,
        ai_config=ai_config,
        top_k=TOP_K * 2,
    )

    # Filter by scope.
    if thread.scope == AskScope.meeting and thread.scope_id:
        hits = [h for h in hits if h["meeting_id"] == str(thread.scope_id)]
    elif thread.scope == AskScope.channel and thread.scope_id:
        meeting_ids = {
            str(mid)
            for (mid,) in (
                await db.execute(
                    select(Meeting.id)
                    .where(Meeting.id.in_(_channel_meeting_ids_subq(thread.scope_id)))
                )
            ).all()
        }
        hits = [h for h in hits if h["meeting_id"] in meeting_ids]

    return [
        Citation(
            meeting_id=h["meeting_id"],
            segment_id=h.get("segment_id"),
            meeting_title=h.get("meeting_title"),
            content=h.get("content") or "",
            speaker_name=h.get("speaker_name"),
            start_time=h.get("start_time"),
            score=float(h.get("score") or 0.0),
        )
        for h in hits[:TOP_K]
    ]


def _channel_meeting_ids_subq(channel_id: uuid.UUID):
    from app.models.intel import ChannelMeeting

    return select(ChannelMeeting.meeting_id).where(ChannelMeeting.channel_id == channel_id)


async def _load_ai_config(db: AsyncSession, user_id: uuid.UUID) -> UserAIConfig | None:
    """Default config first, then any active config."""
    rows = await db.execute(
        select(UserAIConfig)
        .where(UserAIConfig.user_id == user_id, UserAIConfig.is_active.is_(True))
        .order_by(UserAIConfig.is_default.desc(), UserAIConfig.created_at.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


def _decrypt_key(config: UserAIConfig) -> str:
    if config.provider in ("vertex_ai", "ollama") and not config.api_key_encrypted:
        return ""
    if not config.api_key_encrypted:
        raise NoAIConfigError(
            "AI provider configured but API key missing. Update Settings → AI Config."
        )
    return _enc.decrypt(config.api_key_encrypted) or ""
