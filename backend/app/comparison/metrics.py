"""Comparison metrics — SteadyStack vs naive weekly DCA.

Pure functions that take a BaselineResult and a TrackerResult and produce
the comparison metrics shown on the user dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.comparison.baseline import BaselineResult
from app.comparison.tracker import TrackedSkip, TrackerResult


@dataclass(frozen=True)
class ComparisonResult:
    """Side-by-side comparison of SteadyStack vs naive DCA."""

    # Cost comparison
    baseline_avg_cost: float
    steadystack_avg_cost: float
    cost_improvement_pct: float  # positive = SteadyStack is cheaper

    # Fee comparison
    baseline_fee_pct: float
    steadystack_fee_pct: float
    fee_improvement_pct: float  # positive = SteadyStack paid less in fees

    # Volume comparison
    baseline_btc_acquired: float
    steadystack_btc_acquired: float
    btc_difference: float  # positive = SteadyStack acquired more

    # Skip effectiveness
    num_skips: int
    justified_skips: int
    skip_accuracy_pct: float  # % of skips that were justified in hindsight

    # Summary
    total_weeks: int
    steadystack_buy_weeks: int
    steadystack_skip_weeks: int


def compare_performance(
    baseline: BaselineResult,
    tracker: TrackerResult,
    weekly_prices: list[float],
    weekly_fees: list[float],
) -> ComparisonResult:
    """Compare SteadyStack's actual performance against naive weekly DCA.

    Args:
        baseline: Result from simulate_baseline().
        tracker: Result from compute_tracker_result().
        weekly_prices: Full series of weekly prices (used for skip validation).
        weekly_fees: Full series of weekly fees (used for skip validation).

    Returns:
        ComparisonResult with all comparison metrics.
    """
    # Cost improvement
    cost_improvement = 0.0
    if baseline.average_cost_per_btc > 0 and tracker.average_cost_per_btc > 0:
        cost_improvement = (
            (baseline.average_cost_per_btc - tracker.average_cost_per_btc)
            / baseline.average_cost_per_btc
            * 100
        )

    # Fee improvement
    fee_improvement = 0.0
    if baseline.fee_pct_of_volume > 0:
        fee_improvement = (
            (baseline.fee_pct_of_volume - tracker.fee_pct_of_volume)
            / baseline.fee_pct_of_volume
            * 100
        )

    # BTC difference
    btc_diff = tracker.total_btc_acquired - baseline.total_btc_acquired

    # Skip accuracy — a skip is "justified" if the price or fees improved
    # within the next 2 weeks compared to the skipped week
    justified = _count_justified_skips(tracker.skips, weekly_prices, weekly_fees)
    skip_accuracy = (justified / len(tracker.skips) * 100) if tracker.skips else 0.0

    total_weeks = len(weekly_prices)

    return ComparisonResult(
        baseline_avg_cost=baseline.average_cost_per_btc,
        steadystack_avg_cost=tracker.average_cost_per_btc,
        cost_improvement_pct=cost_improvement,
        baseline_fee_pct=baseline.fee_pct_of_volume,
        steadystack_fee_pct=tracker.fee_pct_of_volume,
        fee_improvement_pct=fee_improvement,
        baseline_btc_acquired=baseline.total_btc_acquired,
        steadystack_btc_acquired=tracker.total_btc_acquired,
        btc_difference=btc_diff,
        num_skips=len(tracker.skips),
        justified_skips=justified,
        skip_accuracy_pct=skip_accuracy,
        total_weeks=total_weeks,
        steadystack_buy_weeks=tracker.num_buys,
        steadystack_skip_weeks=tracker.num_skips,
    )


def _count_justified_skips(
    skips: tuple[TrackedSkip, ...],
    weekly_prices: list[float],
    weekly_fees: list[float],
    lookahead_weeks: int = 2,
) -> int:
    """Count how many skips were justified in hindsight.

    A skip is justified if within the next `lookahead_weeks` weeks,
    either the price dropped or fees decreased compared to the skipped week.
    """
    justified = 0

    for skip in skips:
        week_idx = skip.week_number - 1  # 0-indexed

        # Look ahead
        found_better = False
        for offset in range(1, lookahead_weeks + 1):
            future_idx = week_idx + offset
            if future_idx >= len(weekly_prices):
                break

            future_price = weekly_prices[future_idx]
            future_fee = weekly_fees[future_idx]

            # Better price OR better fees = justified
            if future_price < skip.price_usd or future_fee < skip.fee_sat_vb:
                found_better = True
                break

        if found_better:
            justified += 1

    return justified
