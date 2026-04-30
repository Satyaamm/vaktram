"""Plan catalog and quota definitions.

Source of truth for what each tier includes. Stripe price IDs are read from
config; the limits below are enforced by app/middleware/quota.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.billing import PlanTier, UsageKind


@dataclass(frozen=True)
class PlanDefinition:
    tier: PlanTier
    name: str
    monthly_price_cents: int  # 0 = free or sales-led
    seat_limit: int  # 0 = unlimited
    limits: dict  # UsageKind -> per-month allowance (0 = unlimited)
    features: set[str]


UNLIMITED = 0

PLANS: dict[PlanTier, PlanDefinition] = {
    PlanTier.free: PlanDefinition(
        tier=PlanTier.free,
        name="Free",
        monthly_price_cents=0,
        seat_limit=1,
        limits={
            UsageKind.transcription_minutes: 60 * 5,  # 5 hours/mo
            UsageKind.bot_minutes: 60 * 2,
            UsageKind.llm_input_tokens: 200_000,
            UsageKind.llm_output_tokens: 50_000,
            UsageKind.storage_gb_hours: 5,
        },
        features={"basic_summary", "watermark"},
    ),
    PlanTier.pro: PlanDefinition(
        tier=PlanTier.pro,
        name="Pro",
        monthly_price_cents=1200,
        seat_limit=1,
        limits={
            UsageKind.transcription_minutes: 60 * 50,
            UsageKind.bot_minutes: 60 * 30,
            UsageKind.llm_input_tokens: 5_000_000,
            UsageKind.llm_output_tokens: 1_500_000,
            UsageKind.storage_gb_hours: 100,
        },
        features={"basic_summary", "byom", "search", "slack_share"},
    ),
    PlanTier.team: PlanDefinition(
        tier=PlanTier.team,
        name="Team",
        monthly_price_cents=2400,
        seat_limit=20,
        limits={
            UsageKind.transcription_minutes: UNLIMITED,
            UsageKind.bot_minutes: UNLIMITED,
            UsageKind.llm_input_tokens: 50_000_000,
            UsageKind.llm_output_tokens: 10_000_000,
            UsageKind.storage_gb_hours: 1_000,
        },
        features={"basic_summary", "byom", "search", "slack_share", "shared_workspace", "integrations"},
    ),
    PlanTier.business: PlanDefinition(
        tier=PlanTier.business,
        name="Business",
        monthly_price_cents=4000,
        seat_limit=200,
        limits={
            UsageKind.transcription_minutes: UNLIMITED,
            UsageKind.bot_minutes: UNLIMITED,
            UsageKind.llm_input_tokens: UNLIMITED,
            UsageKind.llm_output_tokens: UNLIMITED,
            UsageKind.storage_gb_hours: 10_000,
        },
        features={
            "basic_summary", "byom", "search", "slack_share", "shared_workspace",
            "integrations", "sso", "audit_log", "priority_support",
        },
    ),
    PlanTier.enterprise: PlanDefinition(
        tier=PlanTier.enterprise,
        name="Enterprise",
        monthly_price_cents=0,  # sales-led
        seat_limit=UNLIMITED,
        limits={
            UsageKind.transcription_minutes: UNLIMITED,
            UsageKind.bot_minutes: UNLIMITED,
            UsageKind.llm_input_tokens: UNLIMITED,
            UsageKind.llm_output_tokens: UNLIMITED,
            UsageKind.storage_gb_hours: UNLIMITED,
        },
        features={
            "basic_summary", "byom", "search", "slack_share", "shared_workspace",
            "integrations", "sso", "scim", "audit_log", "priority_support",
            "byok", "custom_retention", "data_residency", "dedicated_support",
            "sla", "dlp", "on_prem",
        },
    ),
}


def plan_for(tier: PlanTier) -> PlanDefinition:
    return PLANS[tier]


def has_feature(tier: PlanTier, feature: str) -> bool:
    return feature in PLANS[tier].features


def limit_for(tier: PlanTier, kind: UsageKind) -> int:
    """Return monthly allowance for kind. 0 means unlimited."""
    return PLANS[tier].limits.get(kind, UNLIMITED)
