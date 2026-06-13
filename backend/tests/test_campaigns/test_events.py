"""Tests for campaign event schemas and factory helpers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.campaigns.events import (
    CampaignEvent,
    CampaignEventSeverity,
    CampaignEventStatus,
    bmri_triggered,
    campaign_paused,
    campaign_started,
    data_source_unavailable,
    exchange_permission_issue,
    fee_guardrail_pause,
    fee_target_adjusted,
    period_missed,
)
from app.campaigns.schemas import CampaignEventType

FROZEN_NOW = datetime(2026, 6, 12, 10, 0, tzinfo=UTC)


def test_campaign_event_defaults_to_open_info_with_timestamp() -> None:
    """CampaignEvent has stable defaults for audit logging."""
    event = CampaignEvent(
        id="event-1",
        campaign_id="core-1",
        type=CampaignEventType.CAMPAIGN_STARTED,
        title="Campaign started",
        message="Core Stack is now active.",
        created_at=FROZEN_NOW,
    )

    assert event.severity == CampaignEventSeverity.INFO
    assert event.status == CampaignEventStatus.OPEN
    assert event.created_at == FROZEN_NOW
    assert event.resolved_at is None
    assert event.actions == ()


def test_resolved_event_requires_resolved_at() -> None:
    """Resolved events must record when they were resolved."""
    with pytest.raises(ValueError, match="resolved_at"):
        CampaignEvent(
            id="event-1",
            campaign_id="core-1",
            type=CampaignEventType.CAMPAIGN_PAUSED,
            title="Campaign paused",
            message="Paused by user.",
            status=CampaignEventStatus.RESOLVED,
            created_at=FROZEN_NOW,
        )


def test_campaign_started_factory_uses_plain_language() -> None:
    """Campaign start event should be user-facing, not internal jargon."""
    event = campaign_started(
        campaign_id="core-1",
        campaign_name="Core Stack",
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.CAMPAIGN_STARTED
    assert event.title == "Core Stack started"
    assert event.message == "Core Stack is now active."
    assert event.created_at == FROZEN_NOW


def test_campaign_paused_factory_can_require_action() -> None:
    """Pause events can carry safe recovery actions."""
    event = campaign_paused(
        campaign_id="core-1",
        campaign_name="Core Stack",
        reason="Network fee exceeds your 2% guardrail.",
        now=FROZEN_NOW,
        actions=("Review fees", "Keep paused"),
    )

    assert event.type == CampaignEventType.CAMPAIGN_PAUSED
    assert event.severity == CampaignEventSeverity.WARNING
    assert event.actions == ("Review fees", "Keep paused")
    assert "Network fee exceeds" in event.message


def test_fee_target_adjusted_event_carries_old_and_new_targets() -> None:
    """Fee target adjustment events preserve audit details for reporting."""
    event = fee_target_adjusted(
        campaign_id="core-1",
        old_sat_vb=1.0,
        new_sat_vb=2.0,
        reason="recent weekly lows moved higher",
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.FEE_TARGET_ADJUSTED
    assert event.title == "Fee target adjusted"
    assert event.metric_snapshot == {
        "old_sat_vb": 1.0,
        "new_sat_vb": 2.0,
        "reason": "recent weekly lows moved higher",
    }
    assert "1.0 → 2.0 sat/vB" in event.message


def test_fee_guardrail_pause_leads_with_fee_percentage() -> None:
    """Fee guardrail pause should lead with fee as % of planned buy."""
    event = fee_guardrail_pause(
        campaign_id="core-1",
        fee_pct_of_buy=3.2,
        guardrail_pct=2.0,
        estimated_fee_usd=1.60,
        buy_amount_usd=50.0,
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.FEE_GUARDRAIL_PAUSE
    assert event.severity == CampaignEventSeverity.ACTION_REQUIRED
    assert event.actions == ("Review fees", "Keep paused")
    assert event.message.startswith("Estimated network fee is 3.2%")
    assert event.metric_snapshot["estimated_fee_usd"] == 1.60


def test_bmri_triggered_leads_with_plain_language() -> None:
    """BMRI trigger should say Bitcoin looks cheap before showing percentile detail."""
    event = bmri_triggered(
        campaign_id="boost-1",
        campaign_name="Bear Market Boost",
        bmri_percentile=9.0,
        entry_threshold=10.0,
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.BMRI_TRIGGERED
    assert event.severity == CampaignEventSeverity.ACTION_REQUIRED
    assert event.title == "Bitcoin looks historically cheap"
    assert "BMRI P9.0" in event.message
    assert event.actions == ("Start campaign", "Not now")


def test_data_source_unavailable_pauses_new_actions() -> None:
    """Data-source failures should degrade safely with retry/cached-data actions."""
    event = data_source_unavailable(
        campaign_id="core-1",
        source="Bitcoin Card",
        stale_after="30 minutes",
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.DATA_SOURCE_UNAVAILABLE
    assert event.severity == CampaignEventSeverity.ERROR
    assert "Campaigns remain paused" in event.message
    assert event.actions == ("Retry", "View cached data")


def test_period_missed_event_avoids_silent_rollover() -> None:
    """Missed cadence periods should surface review rather than silently stacking buys."""
    event = period_missed(
        campaign_id="core-1",
        period_label="week of 2026-06-08",
        reason="fee target was not reached before deadline",
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.PERIOD_MISSED
    assert event.severity == CampaignEventSeverity.ACTION_REQUIRED
    assert "week of 2026-06-08" in event.message
    assert event.actions == ("Review campaign", "Skip period")


def test_exchange_permission_issue_recommends_advisory_fallback() -> None:
    """Automation failures should pause safely and offer advisory fallback."""
    event = exchange_permission_issue(
        campaign_id="core-1",
        exchange="Kraken",
        now=FROZEN_NOW,
    )

    assert event.type == CampaignEventType.EXCHANGE_PERMISSION_ISSUE
    assert event.severity == CampaignEventSeverity.ERROR
    assert event.title == "Automation paused safely"
    assert "Kraken" in event.message
    assert event.actions == ("Reconnect key", "Use advisory mode")
