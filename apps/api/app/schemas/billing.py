"""Pydantic schemas for the billing surface."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.billing import PlanTier, SubscriptionStatus, UsageKind


class CheckoutRequest(BaseModel):
    plan: PlanTier
    seats: int = Field(default=1, ge=1, le=10_000)
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str


class PortalRequest(BaseModel):
    return_url: str


class PortalResponse(BaseModel):
    url: str


class SubscriptionRead(BaseModel):
    plan: PlanTier
    status: SubscriptionStatus
    seats: int
    trial_ends_at: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False

    model_config = ConfigDict(from_attributes=True)


class UsageSummaryEntry(BaseModel):
    kind: UsageKind
    used: int
    limit: int  # 0 = unlimited
    remaining: int  # -1 = unlimited


class UsageSummary(BaseModel):
    plan: PlanTier
    period_start: datetime
    entries: list[UsageSummaryEntry]
