"""Tests for campaign state transitions."""

from __future__ import annotations

import pytest

from app.campaigns.schemas import CampaignStatus
from app.campaigns.state import TransitionContext, assert_transition_allowed, transition_allowed


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (CampaignStatus.DRAFT, CampaignStatus.WAITING),
        (CampaignStatus.DRAFT, CampaignStatus.ACTIVE),
        (CampaignStatus.WAITING, CampaignStatus.READY),
        (CampaignStatus.READY, CampaignStatus.ACTIVE),
        (CampaignStatus.ACTIVE, CampaignStatus.PAUSED),
        (CampaignStatus.ACTIVE, CampaignStatus.NEEDS_REVIEW),
        (CampaignStatus.ACTIVE, CampaignStatus.COMPLETED),
        (CampaignStatus.ACTIVE, CampaignStatus.STOPPED),
        (CampaignStatus.PAUSED, CampaignStatus.STOPPED),
        (CampaignStatus.NEEDS_REVIEW, CampaignStatus.ACTIVE),
        (CampaignStatus.NEEDS_REVIEW, CampaignStatus.PAUSED),
        (CampaignStatus.NEEDS_REVIEW, CampaignStatus.STOPPED),
        (CampaignStatus.READY, CampaignStatus.WAITING),
    ],
)
def test_spec_allowed_transitions_pass(source: CampaignStatus, target: CampaignStatus) -> None:
    """State transitions from spec §8.1 are allowed."""
    assert transition_allowed(source, target, TransitionContext(user_confirmed=True)) is True


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (CampaignStatus.COMPLETED, CampaignStatus.ACTIVE),
        (CampaignStatus.STOPPED, CampaignStatus.ACTIVE),
        (CampaignStatus.COMPLETED, CampaignStatus.WAITING),
        (CampaignStatus.STOPPED, CampaignStatus.WAITING),
    ],
)
def test_terminal_campaigns_do_not_reactivate(
    source: CampaignStatus,
    target: CampaignStatus,
) -> None:
    """Completed/stopped campaigns are terminal; clone instead of reactivating."""
    assert transition_allowed(source, target, TransitionContext(user_confirmed=True)) is False


def test_paused_to_active_requires_explicit_confirmation() -> None:
    """Paused campaigns must not silently resume without user confirmation."""
    assert (
        transition_allowed(
            CampaignStatus.PAUSED,
            CampaignStatus.ACTIVE,
            TransitionContext(user_confirmed=False),
        )
        is False
    )
    assert (
        transition_allowed(
            CampaignStatus.PAUSED,
            CampaignStatus.ACTIVE,
            TransitionContext(user_confirmed=True),
        )
        is True
    )


def test_waiting_campaign_with_stale_bmri_remains_waiting() -> None:
    """Stale BMRI must not move a waiting campaign to ready."""
    assert (
        transition_allowed(
            CampaignStatus.WAITING,
            CampaignStatus.READY,
            TransitionContext(fresh_bmri=False),
        )
        is False
    )


def test_assert_transition_allowed_raises_clear_error() -> None:
    """Strict validator raises a helpful ValueError for invalid transitions."""
    with pytest.raises(ValueError, match="completed -> active"):
        assert_transition_allowed(
            CampaignStatus.COMPLETED,
            CampaignStatus.ACTIVE,
            TransitionContext(user_confirmed=True),
        )
