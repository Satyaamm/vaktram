"""
LiteLLM-based meeting summarization.
Generates summaries, action items, decisions, and follow-ups from transcripts.
"""

import logging
import os
from typing import Any, Dict

import litellm

from prompts.summary import SUMMARY_PROMPT
from prompts.action_items import ACTION_ITEMS_PROMPT
from prompts.decisions import DECISIONS_PROMPT
from prompts.follow_ups import FOLLOW_UPS_PROMPT

logger = logging.getLogger(__name__)

# LiteLLM model configuration
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))


class Summarizer:
    """Generates structured meeting summaries using LLM via LiteLLM."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def _call_llm(self, system_prompt: str, transcript: str) -> str:
        """Make an async LLM call via LiteLLM."""
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    async def generate_summary(self, transcript: str) -> str:
        """Generate a concise meeting summary."""
        logger.info("Generating summary...")
        return await self._call_llm(SUMMARY_PROMPT, transcript)

    async def generate_action_items(self, transcript: str) -> str:
        """Extract action items from the transcript."""
        logger.info("Extracting action items...")
        return await self._call_llm(ACTION_ITEMS_PROMPT, transcript)

    async def generate_decisions(self, transcript: str) -> str:
        """Extract key decisions from the transcript."""
        logger.info("Extracting decisions...")
        return await self._call_llm(DECISIONS_PROMPT, transcript)

    async def generate_follow_ups(self, transcript: str) -> str:
        """Extract follow-up items from the transcript."""
        logger.info("Extracting follow-ups...")
        return await self._call_llm(FOLLOW_UPS_PROMPT, transcript)

    async def generate_all(self, transcript: str) -> Dict[str, Any]:
        """Run all generation tasks and return combined results."""
        import asyncio

        summary, action_items, decisions, follow_ups = await asyncio.gather(
            self.generate_summary(transcript),
            self.generate_action_items(transcript),
            self.generate_decisions(transcript),
            self.generate_follow_ups(transcript),
        )

        return {
            "summary": summary,
            "action_items": action_items,
            "decisions": decisions,
            "follow_ups": follow_ups,
        }
