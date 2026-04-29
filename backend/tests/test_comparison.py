"""Tests for the comparison module — baseline, tracker, metrics, and API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.comparison.baseline import simulate_baseline
from app.comparison.metrics import compare_performance
from app.comparison.tracker import TrackedBuy, TrackedSkip, compute_tracker_result
from app.main import app

client = TestClient(app)

# --- Test data: 8 weeks of simulated market conditions ---

WEEKLY_PRICES = [
    65000.0,  # Week 1: neutral
    63000.0,  # Week 2: dip
    64500.0,  # Week 3: recovery
    68000.0,  # Week 4: premium
    62000.0,  # Week 5: bigger dip
    66000.0,  # Week 6: recovery
    67500.0,  # Week 7: slight premium
    64000.0,  # Week 8: dip
]

WEEKLY_FEES = [
    12.0,   # Week 1: low
    15.0,   # Week 2: low
    45.0,   # Week 3: moderate
    90.0,   # Week 4: high
    10.0,   # Week 5: very low
    25.0,   # Week 6: moderate
    80.0,   # Week 7: high
    8.0,    # Week 8: very low
]


class TestBaseline:
    def test_simple_baseline(self) -> None:
        """Baseline buys every week at market price."""
        result = simulate_baseline(
            weekly_prices=WEEKLY_PRICES,
            weekly_fees=WEEKLY_FEES,
            weekly_amount_usd=100.0,
        )

        assert result.num_buys == 8
        assert result.total_invested_usd == 800.0
        assert result.total_btc_acquired > 0
        assert result.total_fees_usd > 0
        assert result.average_cost_per_btc > 0
        assert result.fee_pct_of_volume > 0

    def test_baseline_skips_zero_price(self) -> None:
        """Baseline skips weeks with zero price."""
        result = simulate_baseline(
            weekly_prices=[65000.0, 0.0, 63000.0],
            weekly_fees=[10.0, 10.0, 10.0],
            weekly_amount_usd=100.0,
        )
        assert result.num_buys == 2

    def test_baseline_mismatched_lengths(self) -> None:
        """Raises ValueError when prices and fees have different lengths."""
        with pytest.raises(ValueError, match="same length"):
            simulate_baseline(
                weekly_prices=[65000.0, 63000.0],
                weekly_fees=[10.0],
                weekly_amount_usd=100.0,
            )

    def test_baseline_empty(self) -> None:
        """Empty input produces zero results."""
        result = simulate_baseline(
            weekly_prices=[], weekly_fees=[], weekly_amount_usd=100.0
        )
        assert result.num_buys == 0
        assert result.total_btc_acquired == 0.0

    def test_baseline_fee_cost_is_realistic(self) -> None:
        """Fee costs should be small relative to buy amount."""
        result = simulate_baseline(
            weekly_prices=[65000.0],
            weekly_fees=[20.0],
            weekly_amount_usd=100.0,
        )
        assert result.num_buys == 1
        buy = result.buys[0]
        # 20 sat/vB * 140 vB = 2800 sats = 0.000028 BTC * $65000 ≈ $1.82
        assert 1.0 < buy.fee_cost_usd < 3.0


class TestTracker:
    def test_tracker_aggregation(self) -> None:
        """Tracker correctly aggregates buys and skips."""
        buys = [
            TrackedBuy(week_number=1, price_usd=65000, fee_sat_vb=12,
                       amount_usd=100, btc_acquired=0.00153, fee_cost_usd=1.09),
            TrackedBuy(week_number=2, price_usd=63000, fee_sat_vb=15,
                       amount_usd=100, btc_acquired=0.00158, fee_cost_usd=1.32),
        ]
        skips = [
            TrackedSkip(week_number=3, price_usd=64500, fee_sat_vb=45,
                        action="skip", reason="Fees elevated"),
        ]
        result = compute_tracker_result(buys, skips)

        assert result.num_buys == 2
        assert result.num_skips == 1
        assert result.total_invested_usd == 200.0
        assert result.total_btc_acquired == pytest.approx(0.00311)
        assert result.average_cost_per_btc > 0

    def test_tracker_empty(self) -> None:
        """Empty tracker produces zero results."""
        result = compute_tracker_result([], [])
        assert result.num_buys == 0
        assert result.total_btc_acquired == 0.0
        assert result.average_cost_per_btc == 0.0


class TestMetrics:
    def test_steadystack_beats_baseline(self) -> None:
        """When SteadyStack skips high-fee/high-price weeks, it outperforms."""
        baseline = simulate_baseline(
            weekly_prices=WEEKLY_PRICES,
            weekly_fees=WEEKLY_FEES,
            weekly_amount_usd=100.0,
        )

        # SteadyStack buys only on dip + low-fee weeks: 1, 2, 5, 8
        # With budget rollover: skip weeks roll their $100 to next buy
        # Week 1: $100, Week 2: $100, Skip 3+4 → Week 5: $300, Skip 6+7 → Week 8: $300
        buy_schedule = {1: 100.0, 2: 100.0, 5: 300.0, 8: 300.0}
        ss_buys = []
        for week_num, amount in buy_schedule.items():
            idx = week_num - 1
            price = WEEKLY_PRICES[idx]
            fee = WEEKLY_FEES[idx]
            fee_cost = (fee * 140.0 / 1e8) * price
            net = amount - fee_cost
            ss_buys.append(
                TrackedBuy(
                    week_number=week_num, price_usd=price, fee_sat_vb=fee,
                    amount_usd=amount, btc_acquired=net / price, fee_cost_usd=fee_cost,
                )
            )

        ss_skips = [
            TrackedSkip(week_number=3, price_usd=64500, fee_sat_vb=45,
                        action="skip", reason="Fees elevated"),
            TrackedSkip(week_number=4, price_usd=68000, fee_sat_vb=90,
                        action="skip", reason="Fees too high + price premium"),
            TrackedSkip(week_number=6, price_usd=66000, fee_sat_vb=25,
                        action="wait", reason="Moderate conditions"),
            TrackedSkip(week_number=7, price_usd=67500, fee_sat_vb=80,
                        action="skip", reason="Fees too high"),
        ]

        tracker = compute_tracker_result(ss_buys, ss_skips)
        comparison = compare_performance(baseline, tracker, WEEKLY_PRICES, WEEKLY_FEES)

        # SteadyStack should have lower average cost (bought at dips)
        assert comparison.cost_improvement_pct > 0
        # SteadyStack should have lower fee percentage (skipped high-fee weeks)
        assert comparison.fee_improvement_pct > 0
        # Skip accuracy should be high (prices/fees improved after most skips)
        assert comparison.skip_accuracy_pct > 50

    def test_skip_accuracy_with_no_skips(self) -> None:
        """No skips means 0% skip accuracy (not an error)."""
        baseline = simulate_baseline(
            weekly_prices=[65000.0],
            weekly_fees=[10.0],
            weekly_amount_usd=100.0,
        )
        tracker = compute_tracker_result(
            [TrackedBuy(week_number=1, price_usd=65000, fee_sat_vb=10,
                        amount_usd=100, btc_acquired=0.00153, fee_cost_usd=0.91)],
            [],
        )
        comparison = compare_performance(baseline, tracker, [65000.0], [10.0])
        assert comparison.skip_accuracy_pct == 0.0
        assert comparison.num_skips == 0


class TestComparisonAPI:
    def test_simulate_endpoint(self) -> None:
        """POST /api/comparison/simulate returns valid comparison with rollover."""
        response = client.post(
            "/api/comparison/simulate",
            json={
                "weekly_prices": WEEKLY_PRICES,
                "weekly_fees": WEEKLY_FEES,
                "weekly_amount_usd": 100.0,
                "steadystack_buy_weeks": [1, 2, 5, 8],
                "steadystack_skip_weeks": [
                    {"week": 3, "action": "skip", "reason": "Fees elevated"},
                    {"week": 4, "action": "skip", "reason": "High fees"},
                    {"week": 6, "action": "wait", "reason": "Moderate"},
                    {"week": 7, "action": "skip", "reason": "High fees"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_weeks"] == 8
        assert data["steadystack_buy_weeks"] == 4
        assert data["steadystack_skip_weeks"] == 4
        assert data["baseline_avg_cost"] > 0
        assert data["steadystack_avg_cost"] > 0
        # With rollover, SteadyStack should acquire MORE BTC (same budget, better timing)
        assert data["btc_difference"] > 0
        assert data["cost_improvement_pct"] > 0
        assert "skip_accuracy_pct" in data
