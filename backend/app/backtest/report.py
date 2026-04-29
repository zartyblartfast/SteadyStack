"""Format backtest results for display and export.

Outputs:
- CLI table (printed to stdout)
- JSON export (for caching or integration with the frontend)
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.backtest.runner import AccBacktestResult, BacktestResult


def print_report(result: BacktestResult) -> None:
    """Print a formatted backtest report to stdout."""
    print()
    print(f"{'=' * 72}")
    print(f"  SteadyStack Backtest Report")
    print(f"  Period: {result.start_date} → {result.end_date}  ({result.total_weeks} weeks)")
    print(f"{'=' * 72}")
    print()

    # Header
    header = (
        f"{'Profile':<15} │ {'Cost Edge':>10} │ {'Fee Save':>9} │ "
        f"{'Extra BTC':>10} │ {'Skip Acc':>9} │ {'Buys':>5} │ {'Skips':>6}"
    )
    separator = "─" * len(header)
    print(header)
    print(separator)

    for name in ["conservative", "balanced", "aggressive"]:
        if name not in result.profiles:
            continue
        p = result.profiles[name]
        print(
            f"{p.profile_name:<15} │ "
            f"{p.cost_improvement_pct:>+9.2f}% │ "
            f"{p.fee_improvement_pct:>+8.2f}% │ "
            f"{p.extra_btc_pct:>+9.2f}% │ "
            f"{p.skip_accuracy_pct:>8.1f}% │ "
            f"{p.buy_weeks:>5} │ "
            f"{p.skip_weeks + p.wait_weeks:>6}"
        )

    print(separator)
    print()

    # Detail per profile
    for name in ["conservative", "balanced", "aggressive"]:
        if name not in result.profiles:
            continue
        p = result.profiles[name]
        print(f"  [{p.profile_name.upper()}]")
        print(f"    Avg cost: Naive ${p.baseline_avg_cost:,.0f}  vs  SS ${p.steadystack_avg_cost:,.0f}")
        print(f"    BTC acquired: Naive {p.baseline_btc:.8f}  vs  SS {p.steadystack_btc:.8f}")
        print(f"    Fee overhead: Naive {p.baseline_fees_pct:.3f}%  vs  SS {p.steadystack_fees_pct:.3f}%")
        print(f"    Weeks: {p.buy_weeks} buys, {p.skip_weeks} skips, {p.wait_weeks} waits")
        print()

    print(f"{'=' * 72}")
    print()


def print_accumulation_report(result: AccBacktestResult) -> None:
    """Print a formatted accumulation backtest report."""
    print()
    print(f"{'=' * 78}")
    print(f"  SteadyStack ACCUMULATION Backtest")
    print(f"  Period: {result.start_date} → {result.end_date}  ({result.total_weeks} weeks)")
    print(f"  Base amount: ${result.weekly_base_amount:.0f}/week")
    print(f"{'=' * 78}")
    print()

    header = (
        f"{'Profile':<15} │ {'Cost Edge':>10} │ {'Extra BTC/$ ':>12} │ "
        f"{'Avg Mult':>9} │ {'Invested':>12} │ {'BTC':>12}"
    )
    separator = "─" * len(header)
    print(header)
    print(separator)

    for name in ["conservative", "balanced", "aggressive"]:
        if name not in result.profiles:
            continue
        p = result.profiles[name]
        print(
            f"{p.profile_name:<15} │ "
            f"{p.cost_improvement_pct:>+9.2f}% │ "
            f"{p.extra_btc_pct:>+10.2f}%  │ "
            f"{p.avg_multiplier:>8.3f}x │ "
            f"${p.total_invested_usd:>10,.0f} │ "
            f"{p.total_btc_acquired:>11.8f}"
        )

    print(separator)
    print()

    for name in ["conservative", "balanced", "aggressive"]:
        if name not in result.profiles:
            continue
        p = result.profiles[name]
        print(f"  [{p.profile_name.upper()}]")
        print(f"    Avg cost: Naive ${p.baseline_avg_cost:,.0f}  vs  SS ${p.avg_cost_per_btc:,.0f}")
        print(f"    BTC acquired: Naive {p.baseline_btc_acquired:.8f}  vs  SS {p.total_btc_acquired:.8f}")
        print(f"    Invested: Naive ${p.baseline_invested_usd:,.0f}  vs  SS ${p.total_invested_usd:,.0f}")
        print(f"    Fees: SS ${p.total_fees_usd:,.2f}")
        print(f"    Multiplier: avg {p.avg_multiplier:.3f}x  (range: ${p.min_single_buy:.0f}–${p.max_single_buy:.0f})")
        print(f"    Weeks: {p.weeks_above_1x} above 1x, {p.weeks_at_1x} normal, {p.weeks_below_1x} below 1x")
        print(f"    Extra sats/dollar vs naive: {p.extra_btc_per_dollar:+.1f}")
        print()

    print(f"{'=' * 78}")
    print()


def export_json(result: BacktestResult, output_path: Path | None = None) -> Path:
    """Export backtest results to JSON.

    Args:
        result: The backtest results.
        output_path: Where to write. Defaults to cache/backtest_results.json.

    Returns:
        Path to the written JSON file.
    """
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "cache" / "backtest_results.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to serialisable dict — skip the nested ComparisonResult for brevity
    export = {
        "start_date": result.start_date,
        "end_date": result.end_date,
        "total_weeks": result.total_weeks,
        "profiles": {},
    }
    for name, p in result.profiles.items():
        export["profiles"][name] = {
            "profile_name": p.profile_name,
            "total_weeks": p.total_weeks,
            "buy_weeks": p.buy_weeks,
            "skip_weeks": p.skip_weeks,
            "wait_weeks": p.wait_weeks,
            "cost_improvement_pct": round(p.cost_improvement_pct, 3),
            "fee_improvement_pct": round(p.fee_improvement_pct, 3),
            "extra_btc_pct": round(p.extra_btc_pct, 3),
            "skip_accuracy_pct": round(p.skip_accuracy_pct, 1),
            "baseline_avg_cost": round(p.baseline_avg_cost, 2),
            "steadystack_avg_cost": round(p.steadystack_avg_cost, 2),
            "baseline_btc": round(p.baseline_btc, 8),
            "steadystack_btc": round(p.steadystack_btc, 8),
            "baseline_fees_pct": round(p.baseline_fees_pct, 4),
            "steadystack_fees_pct": round(p.steadystack_fees_pct, 4),
        }

    with open(output_path, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Results exported to: {output_path}")
    return output_path
