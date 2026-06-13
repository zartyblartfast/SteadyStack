"""Tests for campaign repository implementations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.campaigns.events import campaign_started, fee_target_adjusted
from app.campaigns.repository import CampaignRepositoryError, InMemoryCampaignRepository
from app.campaigns.schemas import (
    Campaign,
    CampaignStatus,
    CampaignType,
    ExecutionMode,
    FeePolicy,
    MonitoringMode,
)


def _campaign(campaign_id: str = "core-1") -> Campaign:
    return Campaign(
        id=campaign_id,
        name="Core Stack",
        type=CampaignType.CORE_DCA,
        status=CampaignStatus.ACTIVE,
        monitoring_mode=MonitoringMode.HOSTED_ADVISORY,
        execution_mode=ExecutionMode.ADVISORY_MANUAL,
        amount_usd=100.0,
        cadence="weekly",
        anchor_date=datetime(2026, 6, 12, 9, 0, tzinfo=UTC),
        timezone="Europe/London",
        fee_policy=FeePolicy(),
    )


def test_create_get_and_list_campaigns() -> None:
    """Repository stores campaigns by id and lists them in insertion order."""
    repo = InMemoryCampaignRepository()
    first = _campaign("core-1")
    second = _campaign("core-2")

    repo.create_campaign(first)
    repo.create_campaign(second)

    assert repo.get_campaign("core-1") == first
    assert repo.get_campaign("missing") is None
    assert repo.list_campaigns() == (first, second)


def test_create_campaign_rejects_duplicate_id() -> None:
    """Campaign ids are unique."""
    repo = InMemoryCampaignRepository()
    campaign = _campaign("core-1")

    repo.create_campaign(campaign)

    with pytest.raises(CampaignRepositoryError, match="already exists"):
        repo.create_campaign(campaign)


def test_update_campaign_replaces_existing_campaign() -> None:
    """Existing campaigns can be replaced by id."""
    repo = InMemoryCampaignRepository()
    campaign = _campaign("core-1")
    updated = campaign.model_copy(update={"status": CampaignStatus.PAUSED})

    repo.create_campaign(campaign)
    repo.update_campaign(updated)

    assert repo.get_campaign("core-1") == updated
    assert repo.list_campaigns() == (updated,)


def test_update_campaign_rejects_missing_campaign() -> None:
    """Updating a missing campaign should fail clearly."""
    repo = InMemoryCampaignRepository()

    with pytest.raises(CampaignRepositoryError, match="not found"):
        repo.update_campaign(_campaign("missing"))


def test_add_and_list_events_in_created_order() -> None:
    """Campaign events are persisted in the order they were added."""
    repo = InMemoryCampaignRepository()
    repo.create_campaign(_campaign("core-1"))
    first = campaign_started(
        campaign_id="core-1",
        campaign_name="Core Stack",
        now=datetime(2026, 6, 12, 10, 0, tzinfo=UTC),
    )
    second = fee_target_adjusted(
        campaign_id="core-1",
        old_sat_vb=1.0,
        new_sat_vb=2.0,
        reason="weekly lows moved higher",
        now=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )

    repo.add_event(first)
    repo.add_event(second)

    assert repo.list_events("core-1") == (first, second)


def test_add_event_rejects_missing_campaign() -> None:
    """Events must refer to an existing campaign."""
    repo = InMemoryCampaignRepository()
    event = campaign_started(
        campaign_id="missing",
        campaign_name="Missing",
        now=datetime(2026, 6, 12, 10, 0, tzinfo=UTC),
    )

    with pytest.raises(CampaignRepositoryError, match="not found"):
        repo.add_event(event)


def test_list_events_for_missing_campaign_returns_empty_tuple() -> None:
    """Listing events for an unknown campaign is safe for read paths."""
    repo = InMemoryCampaignRepository()

    assert repo.list_events("missing") == ()
