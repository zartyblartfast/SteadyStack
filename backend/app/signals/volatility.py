"""Volatility and moving average calculations from price history.

Pure functions — no I/O, no side effects. These accept PriceHistory
and return computed values for use in the SignalSnapshot.
"""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.signals.history import PriceHistory


def compute_moving_average(history: PriceHistory, days: int) -> float | None:
    """Compute a simple moving average over the last N days of price history.

    Args:
        history: Historical price points (timestamp_ms, price_usd).
        days: Number of days to average over.

    Returns:
        The average price, or None if insufficient data.
    """
    if not history.prices:
        return None

    ms_per_day = 86_400_000
    latest_ts = history.prices[-1][0]
    cutoff = latest_ts - (days * ms_per_day)

    prices_in_window = [p for ts, p in history.prices if ts >= cutoff]

    if not prices_in_window:
        return None

    return statistics.mean(prices_in_window)


def compute_volatility(history: PriceHistory, days: int) -> float | None:
    """Compute price volatility as the standard deviation of hourly returns.

    Returns the value as a percentage. For example, 2.5 means 2.5% volatility.

    Args:
        history: Historical price points (timestamp_ms, price_usd).
        days: Number of days to compute volatility over.

    Returns:
        Volatility as a percentage, or None if insufficient data.
    """
    if not history.prices or len(history.prices) < 2:
        return None

    ms_per_day = 86_400_000
    latest_ts = history.prices[-1][0]
    cutoff = latest_ts - (days * ms_per_day)

    prices_in_window = [p for ts, p in history.prices if ts >= cutoff]

    if len(prices_in_window) < 2:
        return None

    returns = []
    for i in range(1, len(prices_in_window)):
        prev = prices_in_window[i - 1]
        curr = prices_in_window[i]
        if prev > 0:
            returns.append((curr - prev) / prev)

    if len(returns) < 2:
        return None

    stdev = statistics.stdev(returns)
    return stdev * 100  # as percentage
