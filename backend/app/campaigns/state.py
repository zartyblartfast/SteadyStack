"""Campaign state transition rules."""

from __future__ import annotations

from dataclasses import dataclass

from app.campaigns.schemas import CampaignStatus


@dataclass(frozen=True)
class TransitionContext:
    """Context needed to evaluate conditional transitions."""

    user_confirmed: bool = False
    fresh_bmri: bool = True


_ALWAYS_ALLOWED: frozenset[tuple[CampaignStatus, CampaignStatus]] = frozenset(
    {
        (CampaignStatus.DRAFT, CampaignStatus.WAITING),
        (CampaignStatus.DRAFT, CampaignStatus.ACTIVE),
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
    }
)

_TERMINAL: frozenset[CampaignStatus] = frozenset(
    {CampaignStatus.COMPLETED, CampaignStatus.STOPPED}
)


def transition_allowed(
    source: CampaignStatus,
    target: CampaignStatus,
    context: TransitionContext | None = None,
) -> bool:
    """Return whether a campaign transition is allowed by the v0.3 state table."""
    ctx = context or TransitionContext()

    if source in _TERMINAL:
        return False

    if source == CampaignStatus.WAITING and target == CampaignStatus.READY:
        return ctx.fresh_bmri

    if source == CampaignStatus.PAUSED and target == CampaignStatus.ACTIVE:
        return ctx.user_confirmed

    return (source, target) in _ALWAYS_ALLOWED


def assert_transition_allowed(
    source: CampaignStatus,
    target: CampaignStatus,
    context: TransitionContext | None = None,
) -> None:
    """Raise ValueError if a campaign transition is not allowed."""
    if not transition_allowed(source, target, context):
        raise ValueError(f"Campaign transition not allowed: {source.value} -> {target.value}")
