"""SteadyStack performance tracker.

Accumulates actual buy decisions made under SteadyStack recommendations
and computes realised performance metrics. Used alongside the baseline
calculator to show comparative results.

Pure functions — no I/O, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackedBuy:
    """A single buy that the user acted on from a SteadyStack recommendation."""

    week_number: int
    price_usd: float
    fee_sat_vb: float
    amount_usd: float
    btc_acquired: float
    fee_cost_usd: float


@dataclass(frozen=True)
class TrackedSkip:
    """A week where SteadyStack recommended SKIP or WAIT."""

    week_number: int
    price_usd: float
    fee_sat_vb: float
    action: str  # "skip" or "wait"
    reason: str


@dataclass(frozen=True)
class TrackerResult:
    """Summary of SteadyStack's actual performance."""

    total_invested_usd: float
    total_btc_acquired: float
    total_fees_usd: float
    average_cost_per_btc: float
    fee_pct_of_volume: float
    num_buys: int
    num_skips: int
    buys: tuple[TrackedBuy, ...]
    skips: tuple[TrackedSkip, ...]


def compute_tracker_result(
    buys: list[TrackedBuy],
    skips: list[TrackedSkip],
) -> TrackerResult:
    """Compute aggregate performance from a list of tracked buys and skips.

    Args:
        buys: List of buys the user executed from SteadyStack recommendations.
        skips: List of skipped weeks.

    Returns:
        TrackerResult with aggregate metrics.
    """
    total_btc = sum(b.btc_acquired for b in buys)
    total_fees = sum(b.fee_cost_usd for b in buys)
    total_invested = sum(b.amount_usd for b in buys)

    avg_cost = total_invested / total_btc if total_btc > 0 else 0.0
    fee_pct = (total_fees / total_invested * 100) if total_invested > 0 else 0.0

    return TrackerResult(
        total_invested_usd=total_invested,
        total_btc_acquired=total_btc,
        total_fees_usd=total_fees,
        average_cost_per_btc=avg_cost,
        fee_pct_of_volume=fee_pct,
        num_buys=len(buys),
        num_skips=len(skips),
        buys=tuple(buys),
        skips=tuple(skips),
    )
