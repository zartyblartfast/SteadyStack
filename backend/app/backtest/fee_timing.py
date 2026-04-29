"""Intra-week fee timing analysis.

Models the real SteadyStack edge: within each week, wait for the lowest-fee
day to execute the buy. Price doesn't move much in a few days, but fees can
vary 5-20x within a week.

Compares:
- Naive DCA: buys on a fixed day (Monday) every week
- Best-fee DCA: buys on the cheapest-fee day within each week
- Worst-fee DCA: buys on the most expensive day (as a reference)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.backtest.data import DailyRow


@dataclass
class WeekBuys:
    """Comparison of buy outcomes for a single week."""

    week_start: str
    # Fixed-day buy (Monday / first available day)
    naive_price: float
    naive_fee_sat_vb: float
    naive_fee_cost_usd: float
    naive_btc: float
    # Best-fee day buy
    best_price: float
    best_fee_sat_vb: float
    best_fee_cost_usd: float
    best_btc: float
    best_day: str  # which day was cheapest
    # Worst-fee day (for reference)
    worst_fee_sat_vb: float
    # Fee range within the week
    fee_range_ratio: float  # worst / best


@dataclass
class FeeTimingResult:
    """Summary of intra-week fee timing analysis."""

    total_weeks: int
    buy_amount_usd: float

    # Naive (fixed-day)
    naive_total_btc: float
    naive_total_fees_usd: float
    naive_avg_cost: float

    # Best-fee timing
    best_total_btc: float
    best_total_fees_usd: float
    best_avg_cost: float

    # Edge
    fee_savings_usd: float
    fee_savings_pct: float  # % of total invested saved on fees
    extra_btc: float
    extra_btc_pct: float
    cost_improvement_pct: float
    extra_sats: int

    # Fee variation stats
    avg_weekly_fee_range_ratio: float  # how much fees vary within a week
    median_weekly_fee_range_ratio: float
    weeks_with_2x_fee_range: int  # weeks where worst/best > 2x
    weeks_with_5x_fee_range: int

    # Per-week detail
    weeks: list[WeekBuys]


def analyse_fee_timing(
    daily_data: dict[str, DailyRow],
    buy_amount_usd: float = 100.0,
    tx_size_vbytes: float = 140.0,
) -> FeeTimingResult:
    """Analyse the edge from buying on the cheapest-fee day each week.

    Args:
        daily_data: Daily rows keyed by ISO date string.
        buy_amount_usd: Fixed weekly DCA amount.
        tx_size_vbytes: Assumed transaction size.

    Returns:
        FeeTimingResult with comparison metrics.
    """
    # Sort dates and compute daily fee proxy
    sorted_dates = sorted(daily_data.keys())
    if not sorted_dates:
        raise ValueError("No daily data provided")

    # Compute fee proxy for each day
    daily_fees: dict[str, float] = {}
    daily_prices: dict[str, float] = {}

    for d in sorted_dates:
        row = daily_data[d]
        if row.price_usd is None or row.price_usd <= 0:
            continue

        daily_prices[d] = row.price_usd

        # Fee proxy: total_fees_usd / daily_tx_count → per-tx fee → sat/vB
        if (
            row.total_fees_usd is not None
            and row.daily_tx_count is not None
            and row.daily_tx_count > 0
        ):
            fee_per_tx_usd = row.total_fees_usd / row.daily_tx_count
            fee_per_tx_sats = (fee_per_tx_usd / row.price_usd) * 1e8
            fee_sat_vb = fee_per_tx_sats / tx_size_vbytes
            daily_fees[d] = fee_sat_vb
        else:
            daily_fees[d] = 20.0  # fallback

    # Group into ISO weeks (Monday-start)
    weeks: dict[str, list[str]] = {}
    for d in sorted_dates:
        if d not in daily_prices:
            continue
        dt = datetime.strptime(d, "%Y-%m-%d")
        week_start = dt - timedelta(days=dt.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(d)

    # Analyse each week
    week_results: list[WeekBuys] = []
    naive_total_btc = 0.0
    naive_total_fees = 0.0
    best_total_btc = 0.0
    best_total_fees = 0.0
    total_invested = 0.0
    fee_ratios: list[float] = []

    for week_key in sorted(weeks.keys()):
        days = weeks[week_key]
        if not days:
            continue

        # Filter to days with valid fee data
        valid_days = [d for d in days if d in daily_fees and d in daily_prices]
        if not valid_days:
            continue

        # Naive: buy on first day of week (Monday or first available)
        naive_day = valid_days[0]
        naive_price = daily_prices[naive_day]
        naive_fee = daily_fees[naive_day]

        # Best-fee: buy on cheapest-fee day
        best_day = min(valid_days, key=lambda d: daily_fees[d])
        best_price = daily_prices[best_day]
        best_fee = daily_fees[best_day]

        # Worst fee (for reference)
        worst_day = max(valid_days, key=lambda d: daily_fees[d])
        worst_fee = daily_fees[worst_day]

        # Fee range ratio
        fee_ratio = worst_fee / best_fee if best_fee > 0 else 1.0

        # Calculate buy outcomes
        def calc_buy(price: float, fee_rate: float) -> tuple[float, float]:
            fee_cost = (fee_rate * tx_size_vbytes / 1e8) * price
            net = buy_amount_usd - fee_cost
            btc = net / price if net > 0 and price > 0 else 0.0
            return btc, fee_cost

        naive_btc, naive_fee_cost = calc_buy(naive_price, naive_fee)
        best_btc, best_fee_cost = calc_buy(best_price, best_fee)

        week_results.append(WeekBuys(
            week_start=week_key,
            naive_price=naive_price,
            naive_fee_sat_vb=round(naive_fee, 1),
            naive_fee_cost_usd=round(naive_fee_cost, 4),
            naive_btc=naive_btc,
            best_price=best_price,
            best_fee_sat_vb=round(best_fee, 1),
            best_fee_cost_usd=round(best_fee_cost, 4),
            best_btc=best_btc,
            best_day=best_day,
            worst_fee_sat_vb=round(worst_fee, 1),
            fee_range_ratio=round(fee_ratio, 2),
        ))

        naive_total_btc += naive_btc
        naive_total_fees += naive_fee_cost
        best_total_btc += best_btc
        best_total_fees += best_fee_cost
        total_invested += buy_amount_usd
        fee_ratios.append(fee_ratio)

    # Compute summary metrics
    naive_avg_cost = total_invested / naive_total_btc if naive_total_btc > 0 else 0.0
    best_avg_cost = total_invested / best_total_btc if best_total_btc > 0 else 0.0

    fee_savings_usd = naive_total_fees - best_total_fees
    fee_savings_pct = (fee_savings_usd / total_invested * 100) if total_invested > 0 else 0.0

    extra_btc = best_total_btc - naive_total_btc
    extra_btc_pct = (extra_btc / naive_total_btc * 100) if naive_total_btc > 0 else 0.0
    extra_sats = int(extra_btc * 1e8)

    cost_improvement = 0.0
    if naive_avg_cost > 0 and best_avg_cost > 0:
        cost_improvement = (naive_avg_cost - best_avg_cost) / naive_avg_cost * 100

    # Fee variation stats
    sorted_ratios = sorted(fee_ratios)
    avg_ratio = sum(fee_ratios) / len(fee_ratios) if fee_ratios else 1.0
    median_ratio = sorted_ratios[len(sorted_ratios) // 2] if sorted_ratios else 1.0
    weeks_2x = sum(1 for r in fee_ratios if r >= 2.0)
    weeks_5x = sum(1 for r in fee_ratios if r >= 5.0)

    return FeeTimingResult(
        total_weeks=len(week_results),
        buy_amount_usd=buy_amount_usd,
        naive_total_btc=naive_total_btc,
        naive_total_fees_usd=round(naive_total_fees, 2),
        naive_avg_cost=round(naive_avg_cost, 2),
        best_total_btc=best_total_btc,
        best_total_fees_usd=round(best_total_fees, 2),
        best_avg_cost=round(best_avg_cost, 2),
        fee_savings_usd=round(fee_savings_usd, 2),
        fee_savings_pct=round(fee_savings_pct, 4),
        extra_btc=extra_btc,
        extra_btc_pct=round(extra_btc_pct, 4),
        cost_improvement_pct=round(cost_improvement, 4),
        extra_sats=extra_sats,
        avg_weekly_fee_range_ratio=round(avg_ratio, 2),
        median_weekly_fee_range_ratio=round(median_ratio, 2),
        weeks_with_2x_fee_range=weeks_2x,
        weeks_with_5x_fee_range=weeks_5x,
        weeks=week_results,
    )


def print_fee_timing_report(result: FeeTimingResult) -> None:
    """Print a formatted fee timing report."""
    print()
    print(f"{'=' * 72}")
    print(f"  Intra-Week Fee Timing Analysis")
    print(f"  {result.total_weeks} weeks, ${result.buy_amount_usd:.0f}/week")
    print(f"{'=' * 72}")
    print()

    print(f"  {'':30} {'Naive (Monday)':>16}   {'Best-Fee Day':>16}")
    print(f"  {'─' * 66}")
    print(f"  {'Total fees paid':<30} ${result.naive_total_fees_usd:>14,.2f}   ${result.best_total_fees_usd:>14,.2f}")
    print(f"  {'Total BTC acquired':<30} {result.naive_total_btc:>15.8f}   {result.best_total_btc:>15.8f}")
    print(f"  {'Avg cost per BTC':<30} ${result.naive_avg_cost:>14,.0f}   ${result.best_avg_cost:>14,.0f}")
    print()

    print(f"  Fee savings:          ${result.fee_savings_usd:,.2f}  ({result.fee_savings_pct:.3f}% of invested)")
    print(f"  Extra BTC:            {result.extra_btc:.8f}  ({result.extra_btc_pct:.3f}%)")
    print(f"  Extra sats:           {result.extra_sats:,}")
    print(f"  Cost improvement:     {result.cost_improvement_pct:.3f}%")
    print()

    print(f"  Weekly fee variation:")
    print(f"    Avg worst/best ratio:    {result.avg_weekly_fee_range_ratio:.1f}x")
    print(f"    Median worst/best ratio: {result.median_weekly_fee_range_ratio:.1f}x")
    print(f"    Weeks with ≥2x range:    {result.weeks_with_2x_fee_range} / {result.total_weeks} ({result.weeks_with_2x_fee_range / result.total_weeks * 100:.0f}%)")
    print(f"    Weeks with ≥5x range:    {result.weeks_with_5x_fee_range} / {result.total_weeks} ({result.weeks_with_5x_fee_range / result.total_weeks * 100:.0f}%)")
    print()
    print(f"{'=' * 72}")
    print()
