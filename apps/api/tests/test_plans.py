"""Plan catalog invariants. Pure data, fast."""

from __future__ import annotations

from app.models.billing import PlanTier
from app.services.plans import PLANS, has_feature, limit_for


def test_every_tier_has_a_plan():
    for tier in PlanTier:
        assert tier in PLANS, f"missing plan for {tier}"
        p = PLANS[tier]
        assert p.name
        assert p.limits is not None
        assert p.features is not None


def test_higher_tiers_include_lower_features():
    """Pro features ⊆ Team ⊆ Business ⊆ Enterprise."""
    pro = PLANS[PlanTier.pro].features
    team = PLANS[PlanTier.team].features
    biz = PLANS[PlanTier.business].features
    ent = PLANS[PlanTier.enterprise].features
    assert pro.issubset(team)
    assert team.issubset(biz)
    assert biz.issubset(ent)


def test_enterprise_unlimited():
    """Enterprise plan should have 0 (unlimited) for every limit kind it lists."""
    ent = PLANS[PlanTier.enterprise]
    for kind, cap in ent.limits.items():
        assert cap == 0, f"enterprise {kind} should be unlimited (got {cap})"


def test_has_feature_lookup():
    assert has_feature(PlanTier.business, "sso")
    assert not has_feature(PlanTier.free, "sso")


def test_limit_for_returns_int():
    from app.models.billing import UsageKind

    cap = limit_for(PlanTier.pro, UsageKind.transcription_minutes)
    assert isinstance(cap, int)
    assert cap > 0
