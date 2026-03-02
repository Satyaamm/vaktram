"""LiteLLM-based BYOM (Bring Your Own Model) integration."""

from __future__ import annotations

import json
from typing import Any

from litellm import acompletion

from app.config import get_settings
from app.models.team import UserProfile
from app.services.encryption_service import EncryptionService

settings = get_settings()

DEFAULT_SUMMARY_PROMPT = """You are an expert meeting assistant. Given the following meeting transcript, produce a structured JSON response with:

1. "summary_text": A concise, well-structured summary (2-4 paragraphs).
2. "action_items": A list of objects with "description", "assignee" (if mentioned), and "due_date" (if mentioned).
3. "key_decisions": A list of objects with "decision" and "context".
4. "topics": A list of main topics discussed.
5. "sentiment": The overall meeting sentiment (positive, neutral, negative, mixed).

Transcript:
{transcript}

Respond ONLY with valid JSON."""


class LLMService:
    def __init__(self):
        self.encryption = EncryptionService()

    async def generate_summary(
        self,
        transcript: str,
        provider: str | None = None,
        model: str | None = None,
        custom_prompt: str | None = None,
        user: UserProfile | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Generate a meeting summary using LiteLLM.

        LiteLLM supports 100+ LLM providers with a unified interface.
        """
        provider = provider or settings.default_llm_provider
        model = model or settings.default_llm_model

        # Build the model string for litellm (e.g. "openai/gpt-4o-mini")
        litellm_model = f"{provider}/{model}" if provider != "openai" else model

        prompt = (custom_prompt or DEFAULT_SUMMARY_PROMPT).format(transcript=transcript)

        # Resolve API key
        resolved_key = api_key or settings.openai_api_key or None

        response = await acompletion(
            model=litellm_model,
            messages=[{"role": "user", "content": prompt}],
            api_key=resolved_key,
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
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

        return result

    async def completion(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generic completion call through LiteLLM."""
        provider = provider or settings.default_llm_provider
        model = model or settings.default_llm_model
        litellm_model = f"{provider}/{model}" if provider != "openai" else model

        response = await acompletion(
            model=litellm_model,
            messages=messages,
            api_key=api_key or settings.openai_api_key or None,
            **kwargs,
        )
        return response.choices[0].message.content
