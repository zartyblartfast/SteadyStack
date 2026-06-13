"""Tests for campaign domain schemas."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.campaigns.schemas import (
    BmriPolicy,
    Campaign,
    CampaignStatus,
    CampaignType,
    ExecutionMode,
    FeeDeadlineAction,
    FeePolicy,
    MonitoringMode,
)


def test_campaign_requires_anchor_date_and_timezone() -> None:
    """Campaigns carry scheduling anchor data needed for deterministic cadence."""
    campaign = Campaign(
        id="core-1",
        name="Core Stack",
        type=CampaignType.CORE_DCA,
        status=CampaignStatus.ACTIVE,
        monitoring_mode=MonitoringMode.HOSTED_ADVISORY,
        execution_mode=ExecutionMode.ADVISORY_MANUAL,
        amount_usd=100.0,
        cadence="weekly",
        anchor_date=datetime.fromisoformat("2026-06-12T09:00:00+00:00"),
        timezone="Europe/London",
        fee_policy=FeePolicy(),
    )

    assert campaign.anchor_date.isoformat() == "2026-06-12T09:00:00+00:00"
    assert campaign.timezone == "Europe/London"
    assert campaign.fee_policy.max_fee_pct_of_buy == 2.0
    assert campaign.fee_policy.on_deadline == FeeDeadlineAction.ASK_USER


def test_default_fee_policy_is_adaptive_and_percentage_guarded() -> None:
    """Default fee policy follows v0.3 spec: adaptive, percentage-led guardrail."""
    policy = FeePolicy()

    assert policy.adaptive is True
    assert policy.max_fee_pct_of_buy == 2.0
    assert policy.estimated_transaction_vbytes == 140
    assert policy.on_deadline == FeeDeadlineAction.ASK_USER


@pytest.mark.parametrize("value", [0.0, -1.0])
def test_fee_policy_rejects_non_positive_buy_percentage_guardrail(value: float) -> None:
    """Fee guardrail as percent of buy must be positive."""
    with pytest.raises(ValueError, match="max_fee_pct_of_buy"):
        FeePolicy(max_fee_pct_of_buy=value)


def test_bmri_policy_defaults_to_p10_entry_and_p5_deep_value() -> None:
    """BMRI policy defaults match Bear Market Boost product rules."""
    policy = BmriPolicy(enabled=True)

    assert policy.entry_percentile == 10.0
    assert policy.deep_value_percentile == 5.0


def test_bmri_policy_rejects_invalid_percentile_order() -> None:
    """Deep value must be below or equal to entry threshold."""
    with pytest.raises(ValueError, match="deep_value_percentile"):
        BmriPolicy(enabled=True, entry_percentile=10.0, deep_value_percentile=20.0)


def test_fixed_term_campaign_requires_end_date_or_total_budget() -> None:
    """Fixed-term DCA must define an end condition."""
    with pytest.raises(ValueError, match="end_date or total_budget_usd"):
        Campaign(
            id="fixed-1",
            name="Fixed Term",
            type=CampaignType.FIXED_TERM_DCA,
            status=CampaignStatus.DRAFT,
            monitoring_mode=MonitoringMode.LOCAL_DEVICE,
            execution_mode=ExecutionMode.ADVISORY_MANUAL,
            amount_usd=200.0,
            cadence="monthly",
            anchor_date=datetime.fromisoformat("2026-06-12T09:00:00+00:00"),
            timezone="Europe/London",
            fee_policy=FeePolicy(),
        )
