"""Shared data types that cross module boundaries.

These are the contracts between signals, policy, and engine.
Kept in one place so that imports always flow inward, never between pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Action(str, Enum):
    """Possible engine decisions."""

    BUY = "buy"
    SKIP = "skip"
    WAIT = "wait"


@dataclass(frozen=True)
class SignalScore:
    """A single scored signal with its reasoning."""

    name: str
    value: float  # normalised 0.0 to 1.0
    weight: float
    reason: str


@dataclass(frozen=True)
class SignalSnapshot:
    """Point-in-time market data collected by the signals module.

    This is the sole input to the policy layer. All fields are optional
    to support degraded operation when a data source is unavailable.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Mempool / fee data
    fee_rate_sat_vb: float | None = None
    mempool_depth_mb: float | None = None
    fastest_fee: float | None = None
    half_hour_fee: float | None = None
    hour_fee: float | None = None
    economy_fee: float | None = None

    # Price data
    price_usd: float | None = None
    price_1h_change_pct: float | None = None
    price_24h_change_pct: float | None = None
    price_7d_change_pct: float | None = None
    price_7d_avg: float | None = None
    price_30d_avg: float | None = None

    # Volatility
    volatility_24h_pct: float | None = None
    volatility_7d_pct: float | None = None

    # Data freshness (seconds since last successful fetch per source)
    staleness_fees_s: float = 0.0
    staleness_price_s: float = 0.0
    staleness_onchain_s: float = 0.0

    @classmethod
    def empty(cls) -> SignalSnapshot:
        """Create a snapshot with no data — used for safety invariant tests."""
        return cls()

    def with_staleness(self, minutes: float) -> SignalSnapshot:
        """Return a copy with all staleness values set to the given minutes."""
        seconds = minutes * 60
        return SignalSnapshot(
            **{
                **self.__dict__,
                "staleness_fees_s": seconds,
                "staleness_price_s": seconds,
                "staleness_onchain_s": seconds,
            }
        )


@dataclass(frozen=True)
class Decision:
    """The output of the engine pipeline."""

    action: Action
    amount_usd: float | None = None
    confidence: float = 1.0  # 0.0 to 1.0
    scores: tuple[SignalScore, ...] = ()
    reason: str = ""
    explanation: str = ""  # human-readable template output
    snapshot: SignalSnapshot | None = None  # the inputs that produced this decision
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
