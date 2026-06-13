"""Campaign event schemas and factory helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.campaigns.schemas import CampaignEventType


class CampaignEventSeverity(StrEnum):
    """User-facing event severity."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ACTION_REQUIRED = "action_required"


class CampaignEventStatus(StrEnum):
    """Event resolution state."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class CampaignEvent(BaseModel):
    """Auditable event emitted by campaign logic."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    type: CampaignEventType
    severity: CampaignEventSeverity = CampaignEventSeverity.INFO
    title: str
    message: str
    metric_snapshot: dict[str, Any] = Field(default_factory=dict)
    actions: tuple[str, ...] = ()
    status: CampaignEventStatus = CampaignEventStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None

    @model_validator(mode="after")
    def resolved_events_need_timestamp(self) -> CampaignEvent:
        """Resolved events must preserve when the user/system resolved them."""
        if self.status == CampaignEventStatus.RESOLVED and self.resolved_at is None:
            raise ValueError("resolved_at is required when status is resolved")
        return self


def campaign_started(
    *,
    campaign_id: str,
    campaign_name: str,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an event for a campaign becoming active."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.CAMPAIGN_STARTED,
        severity=CampaignEventSeverity.SUCCESS,
        title=f"{campaign_name} started",
        message=f"{campaign_name} is now active.",
        created_at=_now(now),
    )


def campaign_paused(
    *,
    campaign_id: str,
    campaign_name: str,
    reason: str,
    now: datetime | None = None,
    actions: tuple[str, ...] = (),
) -> CampaignEvent:
    """Create an event for a campaign pause."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.CAMPAIGN_PAUSED,
        severity=CampaignEventSeverity.WARNING,
        title=f"{campaign_name} paused",
        message=f"{campaign_name} is paused. {reason}",
        actions=actions,
        created_at=_now(now),
    )


def fee_target_adjusted(
    *,
    campaign_id: str,
    old_sat_vb: float,
    new_sat_vb: float,
    reason: str,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an event when adaptive fee policy changes the target."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.FEE_TARGET_ADJUSTED,
        severity=CampaignEventSeverity.INFO,
        title="Fee target adjusted",
        message=(
            f"Recommended fee target changed from {old_sat_vb} → {new_sat_vb} "
            f"sat/vB because {reason}."
        ),
        metric_snapshot={
            "old_sat_vb": old_sat_vb,
            "new_sat_vb": new_sat_vb,
            "reason": reason,
        },
        created_at=_now(now),
    )


def fee_guardrail_pause(
    *,
    campaign_id: str,
    fee_pct_of_buy: float,
    guardrail_pct: float,
    estimated_fee_usd: float,
    buy_amount_usd: float,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an action-required event when fees exceed campaign guardrails."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.FEE_GUARDRAIL_PAUSE,
        severity=CampaignEventSeverity.ACTION_REQUIRED,
        title="Network fee exceeds guardrail",
        message=(
            f"Estimated network fee is {fee_pct_of_buy:.1f}% of your "
            f"${buy_amount_usd:.0f} buy. Your limit is {guardrail_pct:.1f}%."
        ),
        metric_snapshot={
            "fee_pct_of_buy": fee_pct_of_buy,
            "guardrail_pct": guardrail_pct,
            "estimated_fee_usd": estimated_fee_usd,
            "buy_amount_usd": buy_amount_usd,
        },
        actions=("Review fees", "Keep paused"),
        created_at=_now(now),
    )


def bmri_triggered(
    *,
    campaign_id: str,
    campaign_name: str,
    bmri_percentile: float,
    entry_threshold: float,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an action-required event for a BMRI value-zone trigger."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.BMRI_TRIGGERED,
        severity=CampaignEventSeverity.ACTION_REQUIRED,
        title="Bitcoin looks historically cheap",
        message=(
            f"{campaign_name} can start. Detail: BMRI P{bmri_percentile:.1f}, "
            f"inside your P{entry_threshold:.1f} value zone."
        ),
        metric_snapshot={
            "bmri_percentile": bmri_percentile,
            "entry_threshold": entry_threshold,
        },
        actions=("Start campaign", "Not now"),
        created_at=_now(now),
    )


def data_source_unavailable(
    *,
    campaign_id: str,
    source: str,
    stale_after: str,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an event for stale/unavailable market data."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.DATA_SOURCE_UNAVAILABLE,
        severity=CampaignEventSeverity.ERROR,
        title="Metrics temporarily unavailable",
        message=(
            f"{source} has not provided fresh data within {stale_after}. "
            "Campaigns remain paused until fresh data is available."
        ),
        metric_snapshot={"source": source, "stale_after": stale_after},
        actions=("Retry", "View cached data"),
        created_at=_now(now),
    )


def period_missed(
    *,
    campaign_id: str,
    period_label: str,
    reason: str,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an event when a cadence period is missed without silent rollover."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.PERIOD_MISSED,
        severity=CampaignEventSeverity.ACTION_REQUIRED,
        title="DCA period missed",
        message=f"The {period_label} period was missed because {reason}.",
        metric_snapshot={"period_label": period_label, "reason": reason},
        actions=("Review campaign", "Skip period"),
        created_at=_now(now),
    )


def exchange_permission_issue(
    *,
    campaign_id: str,
    exchange: str,
    now: datetime | None = None,
) -> CampaignEvent:
    """Create an event when exchange automation permissions are invalid."""
    return CampaignEvent(
        campaign_id=campaign_id,
        type=CampaignEventType.EXCHANGE_PERMISSION_ISSUE,
        severity=CampaignEventSeverity.ERROR,
        title="Automation paused safely",
        message=(
            f"{exchange} key no longer has buy permission. "
            "No buys will be attempted until you reconnect."
        ),
        metric_snapshot={"exchange": exchange},
        actions=("Reconnect key", "Use advisory mode"),
        created_at=_now(now),
    )


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)
