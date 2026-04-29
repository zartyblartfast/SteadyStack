"""Signal collector — orchestrates all signal fetches into a SignalSnapshot.

This is the entry point for the signals module. It fetches data from all sources
(with caching and fallback), computes derived values, and returns a single
SignalSnapshot for the policy layer.

The collector has no knowledge of policy rules or decisions.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict

from app.config import settings
from app.schemas import SignalSnapshot
from app.signals.cache import cache_get, cache_set
from app.signals.exceptions import SignalFetchError
from app.signals.mempool import FeeEstimates, MempoolInfo, fetch_fee_estimates, fetch_mempool_info
from app.signals.price import (
    PriceData,
    PriceHistory,
    fetch_price_binance,
    fetch_price_coingecko,
    fetch_price_history_coingecko,
)
from app.signals.volatility import compute_moving_average, compute_volatility

logger = logging.getLogger(__name__)

# Cache keys
CACHE_KEY_FEES = "signals:fees"
CACHE_KEY_MEMPOOL = "signals:mempool"
CACHE_KEY_PRICE = "signals:price"
CACHE_KEY_HISTORY = "signals:price_history"


async def collect_signals() -> SignalSnapshot:
    """Collect all market signals and return a unified snapshot.

    Fetches fee estimates, price data, and price history (for moving averages
    and volatility). Uses caching and fallback sources. Tracks staleness
    for each data category.

    Returns:
        A SignalSnapshot with all available data. Missing data is None.
    """
    fees, fees_age = await _fetch_fees_cached()
    mempool = await _fetch_mempool_cached()
    price, price_age = await _fetch_price_cached()
    history = await _fetch_history_cached()

    # Compute derived values from history
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
        fee_rate_sat_vb=fees.hour_fee if fees else None,
        fastest_fee=fees.fastest_fee if fees else None,
        half_hour_fee=fees.half_hour_fee if fees else None,
        hour_fee=fees.hour_fee if fees else None,
        economy_fee=fees.economy_fee if fees else None,
        mempool_depth_mb=mempool.size_mb if mempool else None,
        # Price data
        price_usd=price.price_usd if price else None,
        price_1h_change_pct=price.price_1h_change_pct if price else None,
        price_24h_change_pct=price.price_24h_change_pct if price else None,
        price_7d_change_pct=price.price_7d_change_pct if price else None,
        price_7d_avg=price_7d_avg,
        price_30d_avg=price_30d_avg,
        # Volatility
        volatility_24h_pct=volatility_24h,
        volatility_7d_pct=volatility_7d,
        # Staleness
        staleness_fees_s=fees_age,
        staleness_price_s=price_age,
        staleness_onchain_s=0.0,
    )


async def _fetch_fees_cached() -> tuple[FeeEstimates | None, float]:
    """Fetch fee estimates with caching. Returns (data, staleness_seconds)."""
    cached = await cache_get(CACHE_KEY_FEES)
    if cached is not None:
        try:
            return FeeEstimates(**cached["data"]), time.time() - cached["fetched_at"]
        except (KeyError, TypeError):
            pass

    try:
        fees = await fetch_fee_estimates()
        await cache_set(
            CACHE_KEY_FEES,
            {"data": asdict(fees), "fetched_at": time.time()},
            ttl_seconds=settings.cache_ttl_fees,
        )
        return fees, 0.0
    except SignalFetchError:
        logger.warning("Failed to fetch fee estimates — no cached data available")
        return None, float(settings.max_data_staleness_minutes * 60)


async def _fetch_mempool_cached() -> MempoolInfo | None:
    """Fetch mempool info with caching."""
    cached = await cache_get(CACHE_KEY_MEMPOOL)
    if cached is not None:
        try:
            return MempoolInfo(**cached)
        except (KeyError, TypeError):
            pass

    try:
        mempool = await fetch_mempool_info()
        await cache_set(CACHE_KEY_MEMPOOL, asdict(mempool), ttl_seconds=settings.cache_ttl_fees)
        return mempool
    except SignalFetchError:
        logger.warning("Failed to fetch mempool info — no cached data available")
        return None


async def _fetch_price_cached() -> tuple[PriceData | None, float]:
    """Fetch price data with caching and Binance fallback. Returns (data, staleness_seconds)."""
    cached = await cache_get(CACHE_KEY_PRICE)
    if cached is not None:
        try:
            return PriceData(**cached["data"]), time.time() - cached["fetched_at"]
        except (KeyError, TypeError):
            pass

    # Primary: CoinGecko
    try:
        price = await fetch_price_coingecko()
        await cache_set(
            CACHE_KEY_PRICE,
            {"data": asdict(price), "fetched_at": time.time()},
            ttl_seconds=settings.cache_ttl_price,
        )
        return price, 0.0
    except SignalFetchError:
        logger.warning("CoinGecko price fetch failed — trying Binance fallback")

    # Fallback: Binance
    try:
        price = await fetch_price_binance()
        await cache_set(
            CACHE_KEY_PRICE,
            {"data": asdict(price), "fetched_at": time.time()},
            ttl_seconds=settings.cache_ttl_price,
        )
        return price, 0.0
    except SignalFetchError:
        logger.warning("Binance price fetch also failed — no price data available")
        return None, float(settings.max_data_staleness_minutes * 60)


async def _fetch_history_cached() -> PriceHistory | None:
    """Fetch price history with caching (used for moving averages and volatility)."""
    cached = await cache_get(CACHE_KEY_HISTORY)
    if cached is not None:
        try:
            prices = tuple(tuple(p) for p in cached["prices"])
            return PriceHistory(prices=prices, source=cached.get("source", "cache"))
        except (KeyError, TypeError):
            pass

    try:
        history = await fetch_price_history_coingecko(days=30)
        await cache_set(
            CACHE_KEY_HISTORY,
            {"prices": list(history.prices), "source": history.source},
            ttl_seconds=settings.cache_ttl_onchain,
        )
        return history
    except SignalFetchError:
        logger.warning("Failed to fetch price history — no cached data available")
        return None
