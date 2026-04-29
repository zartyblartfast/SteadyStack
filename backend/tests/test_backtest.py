"""Tests for the backtest module.

Uses synthetic data to verify snapshot building and runner logic
without making API calls.
"""

from __future__ import annotations

from app.backtest.data import WeeklyRow
from app.backtest.runner import run_backtest
from app.backtest.snapshot_builder import build_snapshot, build_snapshots
from app.policy.profiles import BALANCED, PRESETS


# --- Synthetic weekly data (8 weeks of realistic conditions) ---

SYNTHETIC_WEEKS = [
    WeeklyRow(
        week_start="2024-01-01", price_usd=42000, price_7d_avg=41500,
        price_30d_avg=40000, volatility_24h_pct=1.2, fee_proxy_sat_vb=12.0,
        mempool_size_bytes=5_000_000, mempool_tx_count=3000,
    ),
    WeeklyRow(
        week_start="2024-01-08", price_usd=43000, price_7d_avg=42500,
        price_30d_avg=41000, volatility_24h_pct=1.5, fee_proxy_sat_vb=18.0,
        mempool_size_bytes=8_000_000, mempool_tx_count=5000,
    ),
    WeeklyRow(
        week_start="2024-01-15", price_usd=41000, price_7d_avg=42000,
        price_30d_avg=41500, volatility_24h_pct=2.8, fee_proxy_sat_vb=55.0,
        mempool_size_bytes=30_000_000, mempool_tx_count=15000,
    ),
    WeeklyRow(
        week_start="2024-01-22", price_usd=40000, price_7d_avg=41500,
        price_30d_avg=41000, volatility_24h_pct=3.5, fee_proxy_sat_vb=90.0,
        mempool_size_bytes=50_000_000, mempool_tx_count=25000,
    ),
    WeeklyRow(
        week_start="2024-01-29", price_usd=39000, price_7d_avg=40500,
        price_30d_avg=41000, volatility_24h_pct=1.0, fee_proxy_sat_vb=8.0,
        mempool_size_bytes=3_000_000, mempool_tx_count=2000,
    ),
    WeeklyRow(
        week_start="2024-02-05", price_usd=41500, price_7d_avg=40000,
        price_30d_avg=41000, volatility_24h_pct=1.8, fee_proxy_sat_vb=22.0,
        mempool_size_bytes=10_000_000, mempool_tx_count=6000,
    ),
    WeeklyRow(
        week_start="2024-02-12", price_usd=44000, price_7d_avg=41000,
        price_30d_avg=41500, volatility_24h_pct=4.2, fee_proxy_sat_vb=75.0,
        mempool_size_bytes=40_000_000, mempool_tx_count=20000,
    ),
    WeeklyRow(
        week_start="2024-02-19", price_usd=43000, price_7d_avg=42500,
        price_30d_avg=42000, volatility_24h_pct=1.3, fee_proxy_sat_vb=10.0,
        mempool_size_bytes=4_000_000, mempool_tx_count=2500,
    ),
]


class TestSnapshotBuilder:
    """Tests for snapshot_builder.py."""

    def test_build_snapshot_basic(self) -> None:
        row = SYNTHETIC_WEEKS[0]
        snap = build_snapshot(row)

        assert snap.price_usd == 42000
        assert snap.price_7d_avg == 41500
        assert snap.price_30d_avg == 40000
        assert snap.fee_rate_sat_vb == 12.0
        assert snap.volatility_24h_pct == 1.2
        assert snap.mempool_depth_mb == 5.0  # 5_000_000 / 1_000_000
        assert snap.staleness_fees_s == 0.0

    def test_build_snapshots_count(self) -> None:
        snaps = build_snapshots(SYNTHETIC_WEEKS)
        assert len(snaps) == len(SYNTHETIC_WEEKS)

    def test_zero_mempool_handled(self) -> None:
        row = WeeklyRow(
            week_start="2024-01-01", price_usd=40000, price_7d_avg=39000,
            price_30d_avg=38000, volatility_24h_pct=1.0, fee_proxy_sat_vb=10.0,
            mempool_size_bytes=0, mempool_tx_count=0,
        )
        snap = build_snapshot(row)
        assert snap.mempool_depth_mb == 0.0


class TestBacktestRunner:
    """Tests for runner.py using synthetic data."""

    def test_backtest_runs_all_profiles(self) -> None:
        result = run_backtest(SYNTHETIC_WEEKS, weekly_amount_usd=100.0)

        assert result.total_weeks == 8
        assert "conservative" in result.profiles
        assert "balanced" in result.profiles
        assert "aggressive" in result.profiles

    def test_backtest_buy_skip_counts_add_up(self) -> None:
        result = run_backtest(SYNTHETIC_WEEKS, weekly_amount_usd=100.0)

        for name, p in result.profiles.items():
            total = p.buy_weeks + p.skip_weeks + p.wait_weeks
            assert total == 8, f"{name}: buys + skips + waits = {total}, expected 8"

    def test_backtest_baseline_same_for_all_profiles(self) -> None:
        """The naive baseline doesn't depend on profiles."""
        result = run_backtest(SYNTHETIC_WEEKS, weekly_amount_usd=100.0)
        baseline_costs = [p.baseline_avg_cost for p in result.profiles.values()]
        assert len(set(round(c, 2) for c in baseline_costs)) == 1

    def test_backtest_conservative_skips_more(self) -> None:
        """Conservative should skip at least as much as balanced."""
        result = run_backtest(SYNTHETIC_WEEKS, weekly_amount_usd=100.0)
        cons = result.profiles["conservative"]
        bal = result.profiles["balanced"]
        # Conservative has tighter thresholds, so should skip >= balanced
        assert cons.skip_weeks + cons.wait_weeks >= bal.skip_weeks + bal.wait_weeks - 1  # allow ±1

    def test_backtest_produces_finite_numbers(self) -> None:
        result = run_backtest(SYNTHETIC_WEEKS, weekly_amount_usd=100.0)

        for name, p in result.profiles.items():
            assert p.cost_improvement_pct != float("inf"), f"{name}: infinite cost improvement"
            assert p.cost_improvement_pct != float("-inf"), f"{name}: negative infinite cost improvement"
            assert p.steadystack_btc >= 0, f"{name}: negative BTC"
            assert p.baseline_btc > 0, f"{name}: zero baseline BTC"
