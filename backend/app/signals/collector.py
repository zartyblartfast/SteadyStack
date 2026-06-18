"""Signal collector backed by Bitcoin Card.

Bitcoin Card is the normal-path source for live Bitcoin metrics. This module
normalizes Bitcoin Card summary/BMRI data into the existing SignalSnapshot
contract used by the legacy policy engine.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.config import settings
from app.schemas import SignalSnapshot
from app.signals.bitcoin_card import (
    BitcoinCardSummary,
    BmriComparison,
    fetch_bmri_comparison,
    fetch_summary,
)
from app.signals.exceptions import SignalFetchError
from app.signals.history import PriceHistory
from app.signals.volatility import compute_moving_average, compute_volatility

logger = logging.getLogger(__name__)


async def collect_signals() -> SignalSnapshot:
    """Collect live Bitcoin metrics from Bitcoin Card.

    Returns:
        A SignalSnapshot with all available data. Missing data is None.
    """
    summary, summary_stale = await _fetch_summary()
    bmri = await _fetch_bmri_history()
    history = _price_history_from_bmri(bmri)

    price_7d_avg: float | None = None
    price_30d_avg: float | None = None
    volatility_24h: float | None = None
    volatility_7d: float | None = None

    if history is not None:
        price_7d_avg = compute_moving_average(history, days=7)
        price_30d_avg = compute_moving_average(history, days=30)
        volatility_24h = compute_volatility(history, days=1)
        volatility_7d = compute_volatility(history, days=7)

    return SignalSnapshot(
        # Fee data
        fee_rate_sat_vb=summary.hour_fee if summary else None,
        fastest_fee=summary.fastest_fee if summary else None,
        half_hour_fee=summary.half_hour_fee if summary else None,
        hour_fee=summary.hour_fee if summary else None,
        economy_fee=summary.minimum_fee if summary else None,
        mempool_depth_mb=None,
        # Price data
        price_usd=summary.price_usd if summary else None,
        price_1h_change_pct=None,
        price_24h_change_pct=None,
        price_7d_change_pct=None,
        price_7d_avg=price_7d_avg,
        price_30d_avg=price_30d_avg,
        # Volatility
        volatility_24h_pct=volatility_24h,
        volatility_7d_pct=volatility_7d,
        # Staleness
        staleness_fees_s=summary_stale,
        staleness_price_s=summary_stale,
        staleness_onchain_s=0.0,
    )


async def _fetch_summary() -> tuple[BitcoinCardSummary | None, float]:
    try:
        return await fetch_summary(), 0.0
    except SignalFetchError:
        logger.warning("Failed to fetch Bitcoin Card summary")
        return None, float(settings.max_data_staleness_minutes * 60)


async def _fetch_bmri_history() -> BmriComparison | None:
    try:
        return await fetch_bmri_comparison()
    except Exception:
        logger.warning("Failed to fetch Bitcoin Card BMRI history")
        return None


def _price_history_from_bmri(bmri: BmriComparison | None) -> PriceHistory | None:
    if bmri is None:
        return None

    prices: list[tuple[int, float]] = []
    for point in bmri.history:
        date_value = point.get("date")
        price_value = point.get("price")
        if not isinstance(date_value, str) or price_value is None:
            continue
        try:
            timestamp_ms = int(
                datetime.fromisoformat(f"{date_value}T00:00:00+00:00").timestamp() * 1000
            )
            prices.append((timestamp_ms, float(price_value)))
        except (TypeError, ValueError):
            continue

    if not prices:
        return None

    prices.sort(key=lambda item: item[0])
    return PriceHistory(prices=tuple(prices), source="bitcoin-card-bmri-history")
