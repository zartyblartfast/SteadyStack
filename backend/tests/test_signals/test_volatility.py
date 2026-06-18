"""Tests for volatility and moving average calculations.

These are pure function tests — no mocking, no I/O.
"""

import pytest

from app.signals.history import PriceHistory
from app.signals.volatility import compute_moving_average, compute_volatility

MS_PER_HOUR = 3_600_000
MS_PER_DAY = 86_400_000

# Base timestamp for test data
T0 = 1_700_000_000_000


def _make_history(prices: list[float], interval_ms: int = MS_PER_HOUR) -> PriceHistory:
    """Helper to build PriceHistory from a flat list of prices."""
    return PriceHistory(
        prices=tuple((T0 + i * interval_ms, p) for i, p in enumerate(prices)),
        source="test",
    )


class TestMovingAverage:
    def test_simple_average(self) -> None:
        """Moving average of [100, 200, 300] over enough days = 200."""
        history = _make_history([100.0, 200.0, 300.0])
        result = compute_moving_average(history, days=1)
        assert result == pytest.approx(200.0)

    def test_windowed_average(self) -> None:
        """Only prices within the window are included."""
        # 5 data points, each 1 day apart
        prices_daily = PriceHistory(
            prices=tuple(
                (T0 + i * MS_PER_DAY, p)
                for i, p in enumerate([100.0, 200.0, 300.0, 400.0, 500.0])
            ),
            source="test",
        )
        # 3-day window: cutoff = day4 - 3 days = day1, so includes days 1-4: 200, 300, 400, 500
        result = compute_moving_average(prices_daily, days=3)
        assert result == pytest.approx(350.0)

    def test_empty_history_returns_none(self) -> None:
        """Returns None for empty price history."""
        empty = PriceHistory(prices=(), source="test")
        assert compute_moving_average(empty, days=7) is None

    def test_single_price(self) -> None:
        """A single price point returns that price as the average."""
        history = _make_history([42000.0])
        result = compute_moving_average(history, days=30)
        assert result == pytest.approx(42000.0)


class TestVolatility:
    def test_zero_volatility(self) -> None:
        """Constant prices have zero volatility."""
        history = _make_history([100.0, 100.0, 100.0, 100.0, 100.0])
        result = compute_volatility(history, days=1)
        assert result == pytest.approx(0.0)

    def test_positive_volatility(self) -> None:
        """Fluctuating prices produce positive volatility."""
        history = _make_history([100.0, 110.0, 95.0, 105.0, 90.0, 108.0])
        result = compute_volatility(history, days=1)
        assert result is not None
        assert result > 0.0

    def test_empty_history_returns_none(self) -> None:
        """Returns None for empty history."""
        empty = PriceHistory(prices=(), source="test")
        assert compute_volatility(empty, days=1) is None

    def test_single_price_returns_none(self) -> None:
        """Returns None for a single price (can't compute returns)."""
        history = _make_history([42000.0])
        assert compute_volatility(history, days=1) is None

    def test_two_prices_returns_none(self) -> None:
        """Returns None for two prices (need at least 2 returns for stdev)."""
        history = _make_history([100.0, 110.0])
        assert compute_volatility(history, days=1) is None

    def test_result_is_percentage(self) -> None:
        """Volatility is returned as a percentage, not a decimal."""
        # 10% swings should produce a volatility value in single/double digits, not 0.0x
        history = _make_history([100.0, 110.0, 100.0, 110.0, 100.0, 110.0])
        result = compute_volatility(history, days=1)
        assert result is not None
        assert result > 1.0  # should be clearly a percentage, not a fraction
