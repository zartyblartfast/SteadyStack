"""Campaign domain schemas.

These types intentionally contain no persistence concerns. They define the
campaign contract used by future API, storage, and policy layers.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - pydantic resolves datetime annotations at runtime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CampaignType(StrEnum):
    """Supported campaign templates/types."""

    CORE_DCA = "core_dca"
    BEAR_MARKET_BOOST = "bear_market_boost"
    FIXED_TERM_DCA = "fixed_term_dca"


class CampaignStatus(StrEnum):
    """Campaign lifecycle states from the v0.3 specification."""

    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    STOPPED = "stopped"


class MonitoringMode(StrEnum):
    """Who monitors campaign conditions and sends alerts."""

    LOCAL_DEVICE = "local_device"
    HOSTED_ADVISORY = "hosted_advisory"
    SELF_HOSTED_AGENT = "self_hosted_agent"


class ExecutionMode(StrEnum):
    """Who executes campaign buys."""

    ADVISORY_MANUAL = "advisory_manual"
    APPROVAL_REQUIRED_AUTOMATION = "approval_required_automation"
    AUTOMATED_LIMITED = "automated_limited"


class FeeDeadlineAction(StrEnum):
    """What to do when the fee target is not reached before the deadline."""

    BUY_BEST_AVAILABLE_WITHIN_GUARDRAILS = "buy_best_available_within_guardrails"
    ASK_USER = "ask_user"
    PAUSE_CAMPAIGN = "pause_campaign"


class BmriExitPolicy(StrEnum):
    """What to do if BMRI rises above the configured value threshold."""

    ALERT_ONLY = "alert_only"
    PAUSE_AFTER_REVIEW = "pause_after_review"
    FIXED_TERM_IGNORE_EXIT = "fixed_term_ignore_exit"


class CampaignEventType(StrEnum):
    """Campaign event types that can be persisted/audited."""

    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_PAUSED = "campaign_paused"
    CAMPAIGN_RESUMED = "campaign_resumed"
    CAMPAIGN_COMPLETED = "campaign_completed"
    BMRI_TRIGGERED = "bmri_triggered"
    BMRI_EXIT_REVIEW = "bmri_exit_review"
    FEE_TARGET_ADJUSTED = "fee_target_adjusted"
    FEE_GUARDRAIL_WARNING = "fee_guardrail_warning"
    FEE_GUARDRAIL_PAUSE = "fee_guardrail_pause"
    BUY_RECOMMENDED = "buy_recommended"
    BUY_MARKED_COMPLETE = "buy_marked_complete"
    MISSED_ALERT = "missed_alert"
    PERIOD_MISSED = "period_missed"
    DATA_SOURCE_UNAVAILABLE = "data_source_unavailable"
    EXCHANGE_PERMISSION_ISSUE = "exchange_permission_issue"


class FeePolicy(BaseModel):
    """Fee optimisation policy for a campaign."""

    model_config = ConfigDict(frozen=True)

    adaptive: bool = True
    max_fee_pct_of_buy: float = Field(default=2.0, gt=0)
    max_fee_usd: float | None = Field(default=None, gt=0)
    max_sat_vb: float | None = Field(default=None, gt=0)
    estimated_transaction_vbytes: int = Field(default=140, gt=0)
    max_wait_days: int | None = Field(default=None, gt=0)
    on_deadline: FeeDeadlineAction = FeeDeadlineAction.ASK_USER


class BmriPolicy(BaseModel):
    """BMRI campaign trigger/review policy."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    entry_percentile: float = Field(default=10.0, ge=0, le=100)
    deep_value_percentile: float = Field(default=5.0, ge=0, le=100)
    exit_policy: BmriExitPolicy = BmriExitPolicy.ALERT_ONLY

    @model_validator(mode="after")
    def deep_value_must_not_exceed_entry(self) -> BmriPolicy:
        """Deep value should be at least as cheap as the entry threshold."""
        if self.deep_value_percentile > self.entry_percentile:
            raise ValueError("deep_value_percentile must be <= entry_percentile")
        return self


class Campaign(BaseModel):
    """Campaign domain object."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    type: CampaignType
    status: CampaignStatus
    monitoring_mode: MonitoringMode
    execution_mode: ExecutionMode
    amount_usd: float = Field(gt=0)
    cadence: Literal["daily", "weekly", "monthly", "custom"]
    anchor_date: datetime
    timezone: str
    fee_policy: FeePolicy
    bmri_policy: BmriPolicy | None = None
    total_budget_usd: float | None = Field(default=None, gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def fixed_term_requires_end_condition(self) -> Campaign:
        """Fixed-term DCA needs a budget or end date so completion is defined."""
        if (
            self.type == CampaignType.FIXED_TERM_DCA
            and self.total_budget_usd is None
            and self.end_date is None
        ):
            raise ValueError("fixed-term campaign requires end_date or total_budget_usd")
        return self
