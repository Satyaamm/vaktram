"""Pydantic schemas for calendar integration."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CalendarConnectionRead(BaseModel):
    id: uuid.UUID
    provider: str
    calendar_id: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarAuthorizeResponse(BaseModel):
    authorization_url: str


class CalendarSyncResponse(BaseModel):
    synced_count: int
    new_meetings: list[str]
