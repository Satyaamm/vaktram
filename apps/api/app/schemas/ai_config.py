"""Pydantic schemas for AI config (BYOM)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIConfigBase(BaseModel):
    provider: str = Field(..., max_length=50)
    model_name: str = Field(..., max_length=100)
    base_url: str | None = None
    is_default: bool = False
    is_active: bool = True


class AIConfigCreate(AIConfigBase):
    api_key: str | None = Field(None, description="Plain-text API key (will be encrypted at rest)")


class AIConfigUpdate(BaseModel):
    provider: str | None = Field(None, max_length=50)
    model_name: str | None = Field(None, max_length=100)
    api_key: str | None = Field(None, description="New API key to encrypt")
    base_url: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class AIConfigRead(AIConfigBase):
    id: uuid.UUID
    user_id: uuid.UUID
    has_api_key: bool = Field(description="Whether an encrypted API key is stored")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
