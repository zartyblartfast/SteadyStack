"""Backtest runner — feeds historical data through the policy engine.

For each strategy profile, iterates week by week:
1. Builds a SignalSnapshot from historical data
2. Calls evaluate_policy() to get BUY/SKIP/WAIT
3. Tracks buys (with budget rollover from skips) and skips
4. Runs the baseline simulator for the same period
5. Compares performance using the existing metrics module

The result is an empirical measurement of the SteadyStack edge per profile.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.backtest.accumulation import ACC_PRESETS, AccumulationProfile, compute_buy_amount
from app.backtest.data import WeeklyRow
from app.backtest.snapshot_builder import build_snapshot
from app.comparison.baseline import BaselineResult, simulate_baseline
from app.comparison.metrics import ComparisonResult, compare_performance
from app.comparison.tracker import TrackedBuy, TrackedSkip, TrackerResult, compute_tracker_result
from app.policy.evaluator import evaluate_policy
from app.policy.profiles import PRESETS, StrategyProfile
from app.schemas import Action


@dataclass
class BacktestProfileResult:
    """Backtest results for a single profile."""

    profile_name: str
    total_weeks: int
    buy_weeks: int
    skip_weeks: int
    wait_weeks: int

    # Empirical edge
    cost_improvement_pct: float
    fee_improvement_pct: float
    extra_btc_pct: float
    skip_accuracy_pct: float

    # Raw numbers
    baseline_avg_cost: float
    steadystack_avg_cost: float
    baseline_btc: float
    steadystack_btc: float
    baseline_fees_pct: float
    steadystack_fees_pct: float

    # Full comparison for deeper analysis
    comparison: ComparisonResult


@dataclass
class BacktestResult:
    """Full backtest results across all profiles."""

    start_date: str
    end_date: str
    total_weeks: int
    profiles: dict[str, BacktestProfileResult]


def run_backtest(
    weekly_data: list[WeeklyRow],
    weekly_amount_usd: float = 100.0,
    profiles: dict[str, StrategyProfile] | None = None,
    tx_size_vbytes: float = 140.0,
) -> BacktestResult:
    """Run the full backtest across all profiles.

    Args:
        weekly_data: Historical weekly data from the data fetcher.
        weekly_amount_usd: Fixed weekly DCA amount in USD.
        profiles: Strategy profiles to test (defaults to all presets).
        tx_size_vbytes: Assumed transaction size for fee calculation.

    Returns:
        BacktestResult with per-profile metrics.
    """
    if profiles is None:
        profiles = PRESETS

    # Extract price and fee series for the baseline simulator
    weekly_prices = [w.price_usd for w in weekly_data]
    weekly_fees = [w.fee_proxy_sat_vb for w in weekly_data]

    # Run naive baseline once (same for all profiles)
    baseline = simulate_baseline(weekly_prices, weekly_fees, weekly_amount_usd, tx_size_vbytes)

    # Run each profile
    profile_results: dict[str, BacktestProfileResult] = {}

    for name, profile in profiles.items():
        result = _run_single_profile(
            weekly_data=weekly_data,
            profile=profile,
            weekly_amount_usd=weekly_amount_usd,
            weekly_prices=weekly_prices,
            weekly_fees=weekly_fees,
            baseline=baseline,
            tx_size_vbytes=tx_size_vbytes,
        )
        profile_results[name] = result

    return BacktestResult(
        start_date=weekly_data[0].week_start if weekly_data else "",
        end_date=weekly_data[-1].week_start if weekly_data else "",
        total_weeks=len(weekly_data),
        profiles=profile_results,
    )


def _run_single_profile(
    weekly_data: list[WeeklyRow],
    profile: StrategyProfile,
    weekly_amount_usd: float,
    weekly_prices: list[float],
    weekly_fees: list[float],
    baseline: BaselineResult,
    tx_size_vbytes: float,
) -> BacktestProfileResult:
    """Run the policy engine week by week for a single profile."""
    buys: list[TrackedBuy] = []
    skips: list[TrackedSkip] = []
    rollover_usd = 0.0
    buy_count = 0
    skip_count = 0
    wait_count = 0

    for i, row in enumerate(weekly_data):
        snapshot = build_snapshot(row)
        decision = evaluate_policy(snapshot, profile)

        week_num = i + 1
        price = row.price_usd
        fee_rate = row.fee_proxy_sat_vb

        if decision.action == Action.BUY and price > 0:
            # Buy with rollover
            buy_amount = weekly_amount_usd + rollover_usd
            rollover_usd = 0.0

            # Fee cost
            fee_cost_usd = (fee_rate * tx_size_vbytes / 1e8) * price
            net_amount = buy_amount - fee_cost_usd

            if net_amount > 0:
                btc_acquired = net_amount / price
                buys.append(TrackedBuy(
                    week_number=week_num,
                    price_usd=price,
                    fee_sat_vb=fee_rate,
                    amount_usd=buy_amount,
                    btc_acquired=btc_acquired,
                    fee_cost_usd=fee_cost_usd,
                ))
                buy_count += 1
            else:
                # Fee exceeds budget — treat as forced skip
                rollover_usd += weekly_amount_usd
                skips.append(TrackedSkip(
                    week_number=week_num,
                    price_usd=price,
                    fee_sat_vb=fee_rate,
                    action="skip",
                    reason=f"Fee cost (${fee_cost_usd:.2f}) exceeds buy amount (${buy_amount:.2f})",
                ))
                skip_count += 1

        elif decision.action == Action.SKIP:
            rollover_usd += weekly_amount_usd
            skips.append(TrackedSkip(
                week_number=week_num,
                price_usd=price,
                fee_sat_vb=fee_rate,
                action="skip",
                reason=decision.reason,
            ))
            skip_count += 1

        else:  # WAIT
            rollover_usd += weekly_amount_usd
            skips.append(TrackedSkip(
                week_number=week_num,
                price_usd=price,
                fee_sat_vb=fee_rate,
                action="wait",
                reason=decision.reason,
            ))
            wait_count += 1

    # Compute tracker result
    tracker = compute_tracker_result(buys, skips)

    # Compare against baseline
    comparison = compare_performance(baseline, tracker, weekly_prices, weekly_fees)

    # Extra BTC as percentage
    extra_btc_pct = 0.0
    if baseline.total_btc_acquired > 0:
        extra_btc_pct = (
            (tracker.total_btc_acquired - baseline.total_btc_acquired)
            / baseline.total_btc_acquired
            * 100
        )

    return BacktestProfileResult(
        profile_name=profile.name,
        total_weeks=len(weekly_data),
        buy_weeks=buy_count,
        skip_weeks=skip_count,
        wait_weeks=wait_count,
        cost_improvement_pct=comparison.cost_improvement_pct,
        fee_improvement_pct=comparison.fee_improvement_pct,
        extra_btc_pct=extra_btc_pct,
        skip_accuracy_pct=comparison.skip_accuracy_pct,
        baseline_avg_cost=comparison.baseline_avg_cost,
        steadystack_avg_cost=comparison.steadystack_avg_cost,
        baseline_btc=comparison.baseline_btc_acquired,
        steadystack_btc=comparison.steadystack_btc_acquired,
        baseline_fees_pct=comparison.baseline_fee_pct,
        steadystack_fees_pct=comparison.steadystack_fee_pct,
        comparison=comparison,
    )


# ── Accumulation-mode backtest ─────────────────────────────────────────


@dataclass
class AccBacktestProfileResult:
    """Backtest results for a single accumulation profile."""

    profile_name: str
    total_weeks: int

    # Accumulation metrics
    total_invested_usd: float
    total_btc_acquired: float
    avg_cost_per_btc: float
    total_fees_usd: float

    # Comparison vs naive
    baseline_invested_usd: float
    baseline_btc_acquired: float
    baseline_avg_cost: float

    # Edges
    cost_improvement_pct: float  # positive = SS is cheaper per BTC
    extra_btc_pct: float  # positive = SS got more BTC
    extra_btc_per_dollar: float  # sats per dollar advantage

    # Behaviour stats
    avg_multiplier: float
    weeks_above_1x: int
    weeks_below_1x: int
    weeks_at_1x: int  # within ±5% of 1.0
    max_single_buy: float
    min_single_buy: float


@dataclass
class AccBacktestResult:
    """Full accumulation backtest results."""

    start_date: str
    end_date: str
    total_weeks: int
    weekly_base_amount: float
    profiles: dict[str, AccBacktestProfileResult]


def run_accumulation_backtest(
    weekly_data: list[WeeklyRow],
    weekly_amount_usd: float = 100.0,
    profiles: dict[str, AccumulationProfile] | None = None,
    tx_size_vbytes: float = 140.0,
) -> AccBacktestResult:
    """Run the accumulation-focused backtest across all profiles.

    Unlike the policy engine backtest, this ALWAYS buys — it just varies
    the amount based on price position and fees.
    """
    if profiles is None:
        profiles = ACC_PRESETS

    # Baseline: naive DCA at fixed amount every week
    weekly_prices = [w.price_usd for w in weekly_data]
    weekly_fees = [w.fee_proxy_sat_vb for w in weekly_data]
    baseline = simulate_baseline(weekly_prices, weekly_fees, weekly_amount_usd, tx_size_vbytes)

    profile_results: dict[str, AccBacktestProfileResult] = {}

    for name, profile in profiles.items():
        result = _run_accumulation_profile(
            weekly_data=weekly_data,
            profile=profile,
            weekly_amount_usd=weekly_amount_usd,
            baseline=baseline,
            tx_size_vbytes=tx_size_vbytes,
        )
        profile_results[name] = result

    return AccBacktestResult(
        start_date=weekly_data[0].week_start if weekly_data else "",
        end_date=weekly_data[-1].week_start if weekly_data else "",
        total_weeks=len(weekly_data),
        weekly_base_amount=weekly_amount_usd,
        profiles=profile_results,
    )


def _run_accumulation_profile(
    weekly_data: list[WeeklyRow],
    profile: AccumulationProfile,
    weekly_amount_usd: float,
    baseline: BaselineResult,
    tx_size_vbytes: float,
) -> AccBacktestProfileResult:
    """Run the accumulation engine week by week for a single profile."""
    total_btc = 0.0
    total_invested = 0.0
    total_fees_usd = 0.0
    multipliers: list[float] = []
    buy_amounts: list[float] = []

    # Track reserve: below-1x weeks save money into reserve,
    # above-1x weeks draw from it. This ensures total investment ≈ naive DCA.
    reserve_usd = 0.0

    for i, row in enumerate(weekly_data):
        # Every 4th week, force-deploy any remaining reserve
        is_month_end = (i + 1) % 4 == 0

        decision = compute_buy_amount(
            base_amount=weekly_amount_usd,
            price_usd=row.price_usd,
            price_30d_avg=row.price_30d_avg,
            fee_sat_vb=row.fee_proxy_sat_vb,
            profile=profile,
            reserve_usd=reserve_usd if is_month_end else 0.0,
            is_month_end=is_month_end,
        )

        raw_amount = decision.buy_amount_usd

        # Budget constraint: cap at base_amount + available reserve
        if raw_amount > weekly_amount_usd:
            extra_needed = raw_amount - weekly_amount_usd
            extra_from_reserve = min(extra_needed, reserve_usd)
            buy_amount = weekly_amount_usd + extra_from_reserve
            reserve_usd -= extra_from_reserve
        else:
            # Below or at base amount — save the difference into reserve
            buy_amount = raw_amount
            reserve_usd += weekly_amount_usd - buy_amount

        # Month-end: deploy remaining reserve on top
        if is_month_end and reserve_usd > 0:
            buy_amount += reserve_usd
            reserve_usd = 0.0

        # Execute buy
        price = row.price_usd
        fee_rate = row.fee_proxy_sat_vb

        if price > 0:
            fee_cost_usd = (fee_rate * tx_size_vbytes / 1e8) * price
            net_amount = buy_amount - fee_cost_usd

            if net_amount > 0:
                btc_acquired = net_amount / price
                total_btc += btc_acquired
                total_fees_usd += fee_cost_usd
                total_invested += buy_amount

        multipliers.append(decision.multiplier)
        buy_amounts.append(buy_amount)

    # Compute metrics
    avg_cost = total_invested / total_btc if total_btc > 0 else 0.0
    avg_mult = sum(multipliers) / len(multipliers) if multipliers else 1.0

    above_1x = sum(1 for m in multipliers if m > 1.05)
    below_1x = sum(1 for m in multipliers if m < 0.95)
    at_1x = len(multipliers) - above_1x - below_1x

    # Cost improvement vs baseline
    cost_improvement = 0.0
    if baseline.average_cost_per_btc > 0 and avg_cost > 0:
        cost_improvement = (
            (baseline.average_cost_per_btc - avg_cost)
            / baseline.average_cost_per_btc * 100
        )

    # Extra BTC comparison — normalise to per-dollar basis
    baseline_btc_per_dollar = (
        baseline.total_btc_acquired / baseline.total_invested_usd
        if baseline.total_invested_usd > 0 else 0.0
    )
    ss_btc_per_dollar = total_btc / total_invested if total_invested > 0 else 0.0

    extra_btc_pct = 0.0
    if baseline_btc_per_dollar > 0:
        extra_btc_pct = (ss_btc_per_dollar - baseline_btc_per_dollar) / baseline_btc_per_dollar * 100

    # Sats per dollar advantage
    extra_sats_per_dollar = (ss_btc_per_dollar - baseline_btc_per_dollar) * 1e8

    return AccBacktestProfileResult(
        profile_name=profile.name,
        total_weeks=len(weekly_data),
        total_invested_usd=round(total_invested, 2),
        total_btc_acquired=total_btc,
        avg_cost_per_btc=avg_cost,
        total_fees_usd=round(total_fees_usd, 2),
        baseline_invested_usd=round(baseline.total_invested_usd, 2),
        baseline_btc_acquired=baseline.total_btc_acquired,
        baseline_avg_cost=baseline.average_cost_per_btc,
        cost_improvement_pct=cost_improvement,
        extra_btc_pct=extra_btc_pct,
        extra_btc_per_dollar=extra_sats_per_dollar,
        avg_multiplier=avg_mult,
        weeks_above_1x=above_1x,
        weeks_below_1x=below_1x,
        weeks_at_1x=at_1x,
        max_single_buy=max(buy_amounts) if buy_amounts else 0.0,
        min_single_buy=min(buy_amounts) if buy_amounts else 0.0,
    )
