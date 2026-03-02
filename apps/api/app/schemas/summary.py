"""Pydantic schemas for meeting summaries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SummaryBase(BaseModel):
    summary_text: str
    action_items: list[dict[str, Any]] | None = None
    key_decisions: list[dict[str, Any]] | None = None
    topics: list[str] | None = None
    sentiment: str | None = None


class SummaryCreate(SummaryBase):
    meeting_id: uuid.UUID
    model_used: str | None = None
    provider_used: str | None = None


class SummaryRead(SummaryBase):
    id: uuid.UUID
    meeting_id: uuid.UUID
    model_used: str | None = None
    provider_used: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SummaryGenerateRequest(BaseModel):
    """Request to generate a summary for a meeting using AI."""
    meeting_id: uuid.UUID
    provider: str | None = Field(None, description="Override LLM provider")
    model: str | None = Field(None, description="Override LLM model")
    custom_prompt: str | None = Field(None, description="Custom summarisation prompt")
