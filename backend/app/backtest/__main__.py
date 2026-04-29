"""CLI entry point for the backtest.

Usage:
    python -m app.backtest                           # default: 2020-01-01 to today, $100/week
    python -m app.backtest --start 2021-01-01        # custom start date
    python -m app.backtest --amount 200              # custom weekly amount
    python -m app.backtest --refresh                 # force re-fetch data (ignore cache)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from app.backtest.data import fetch_and_cache, _fetch_daily
from app.backtest.fee_timing import analyse_fee_timing, print_fee_timing_report
from app.backtest.report import export_json, print_accumulation_report, print_report
from app.backtest.runner import run_accumulation_backtest, run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run SteadyStack backtest against historical BTC data"
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=date(2020, 1, 1),
        help="Start date (ISO format, default: 2020-01-01)",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=None,
        help="End date (ISO format, default: today)",
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=100.0,
        help="Weekly DCA amount in USD (default: 100)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-fetch data from APIs (ignore cache)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export results to JSON",
    )
    parser.add_argument(
        "--mode",
        choices=["policy", "accumulation", "fees", "all"],
        default="all",
        help="Engine mode to test (default: all)",
    )

    args = parser.parse_args()

    print(f"Fetching historical data ({args.start} → {args.end or 'today'})...")
    try:
        weekly_data = fetch_and_cache(
            start_date=args.start,
            end_date=args.end,
            force_refresh=args.refresh,
        )
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Got {len(weekly_data)} weeks of data.")

    if args.mode in ("policy", "all"):
        print(f"Running POLICY engine backtest (${args.amount:.0f}/week)...")
        policy_result = run_backtest(weekly_data, weekly_amount_usd=args.amount)
        print_report(policy_result)
        if args.json:
            export_json(policy_result)

    if args.mode in ("accumulation", "all"):
        print(f"Running ACCUMULATION engine backtest (${args.amount:.0f}/week)...")
        acc_result = run_accumulation_backtest(weekly_data, weekly_amount_usd=args.amount)
        print_accumulation_report(acc_result)

    if args.mode in ("fees", "all"):
        print(f"Fetching daily data for fee timing analysis...")
        daily_data = _fetch_daily(args.start, args.end or date.today())
        print(f"Running INTRA-WEEK FEE TIMING analysis (${args.amount:.0f}/week)...")
        fee_result = analyse_fee_timing(daily_data, buy_amount_usd=args.amount)
        print_fee_timing_report(fee_result)


if __name__ == "__main__":
    main()
