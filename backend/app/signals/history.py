"""Signal history value objects.

These are pure data contracts with no upstream API dependency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceHistory:
    """Historical BTC price points as (timestamp_ms, price_usd)."""

    prices: tuple[tuple[int, float], ...]
    source: str
