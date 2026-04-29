"""Comparison API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.comparison.baseline import simulate_baseline
from app.comparison.metrics import compare_performance
from app.comparison.tracker import TrackedBuy, TrackedSkip, compute_tracker_result

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


class SimulateRequest(BaseModel):
    """Request body for running a comparison simulation.

    Used for demo/backtesting — accepts historical data directly.
    In production, this data comes from stored decision logs.
    """

    weekly_prices: list[float] = Field(
        description="BTC price at each weekly buy point (USD)"
    )
    weekly_fees: list[float] = Field(
        description="Average mempool fee at each weekly buy point (sat/vB)"
    )
    weekly_amount_usd: float = Field(
        default=100.0, description="Fixed weekly buy amount in USD"
    )
    steadystack_buy_weeks: list[int] = Field(
        description="1-indexed week numbers where SteadyStack recommended and user executed a buy"
    )
    steadystack_skip_weeks: list[dict[str, Any]] = Field(
        default=[],
        description="Weeks where SteadyStack recommended skip/wait. "
        "Each item: {week: int, action: str, reason: str}",
    )


class ComparisonResponse(BaseModel):
    """Response body for a comparison result."""

    baseline_avg_cost: float
    steadystack_avg_cost: float
    cost_improvement_pct: float
    baseline_fee_pct: float
    steadystack_fee_pct: float
    fee_improvement_pct: float
    baseline_btc_acquired: float
    steadystack_btc_acquired: float
    btc_difference: float
    num_skips: int
    justified_skips: int
    skip_accuracy_pct: float
    total_weeks: int
    steadystack_buy_weeks: int
    steadystack_skip_weeks: int


@router.post("/simulate", response_model=ComparisonResponse)
async def simulate_comparison(request: SimulateRequest) -> ComparisonResponse:
    """Run a comparison simulation with provided historical data.

    Computes both naive weekly DCA and SteadyStack performance, then
    returns a side-by-side comparison.
    """
    # Baseline: naive weekly DCA
    baseline = simulate_baseline(
        weekly_prices=request.weekly_prices,
        weekly_fees=request.weekly_fees,
        weekly_amount_usd=request.weekly_amount_usd,
    )

    # Build tracked buys with budget rollover.
    # When SteadyStack skips a week, that week's budget rolls forward
    # to the next buy window. This ensures both strategies deploy the
    # same total capital, making the comparison fair.
    buy_weeks_set = set(request.steadystack_buy_weeks)
    skip_weeks_set = {s["week"] for s in request.steadystack_skip_weeks}
    all_weeks = sorted(buy_weeks_set | skip_weeks_set)

    buys: list[TrackedBuy] = []
    rollover = 0.0

    for week_num in all_weeks:
        if week_num in buy_weeks_set:
            idx = week_num - 1
            if 0 <= idx < len(request.weekly_prices):
                price = request.weekly_prices[idx]
                fee = request.weekly_fees[idx]
                buy_amount = request.weekly_amount_usd + rollover
                fee_cost = (fee * 140.0 / 1e8) * price
                net = buy_amount - fee_cost
                if net > 0 and price > 0:
                    buys.append(
                        TrackedBuy(
                            week_number=week_num,
                            price_usd=price,
                            fee_sat_vb=fee,
                            amount_usd=buy_amount,
                            btc_acquired=net / price,
                            fee_cost_usd=fee_cost,
                        )
                    )
                    rollover = 0.0
        else:
            # Skip/wait — budget rolls forward
            rollover += request.weekly_amount_usd

    # Build tracked skips
    skips: list[TrackedSkip] = []
    for skip_data in request.steadystack_skip_weeks:
        week_num = skip_data["week"]
        idx = week_num - 1
        if 0 <= idx < len(request.weekly_prices):
            skips.append(
                TrackedSkip(
                    week_number=week_num,
                    price_usd=request.weekly_prices[idx],
                    fee_sat_vb=request.weekly_fees[idx],
                    action=skip_data.get("action", "skip"),
                    reason=skip_data.get("reason", ""),
                )
            )

    tracker = compute_tracker_result(buys, skips)

    comparison = compare_performance(
        baseline=baseline,
        tracker=tracker,
        weekly_prices=request.weekly_prices,
        weekly_fees=request.weekly_fees,
    )

    return ComparisonResponse(
        baseline_avg_cost=round(comparison.baseline_avg_cost, 2),
        steadystack_avg_cost=round(comparison.steadystack_avg_cost, 2),
        cost_improvement_pct=round(comparison.cost_improvement_pct, 2),
        baseline_fee_pct=round(comparison.baseline_fee_pct, 4),
        steadystack_fee_pct=round(comparison.steadystack_fee_pct, 4),
        fee_improvement_pct=round(comparison.fee_improvement_pct, 2),
        baseline_btc_acquired=comparison.baseline_btc_acquired,
        steadystack_btc_acquired=comparison.steadystack_btc_acquired,
        btc_difference=comparison.btc_difference,
        num_skips=comparison.num_skips,
        justified_skips=comparison.justified_skips,
        skip_accuracy_pct=round(comparison.skip_accuracy_pct, 1),
        total_weeks=comparison.total_weeks,
        steadystack_buy_weeks=comparison.steadystack_buy_weeks,
        steadystack_skip_weeks=comparison.steadystack_skip_weeks,
    )
