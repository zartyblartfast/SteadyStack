"""Price data clients — CoinGecko (primary) and Binance (fallback)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import settings
from app.signals.exceptions import SignalFetchError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceData:
    """BTC price data with change percentages and moving averages."""

    price_usd: float
    price_1h_change_pct: float | None = None
    price_24h_change_pct: float | None = None
    price_7d_change_pct: float | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class PriceHistory:
    """Historical price points for moving average and volatility calculation."""

    prices: tuple[tuple[float, float], ...]  # (timestamp_ms, price_usd)
    source: str = "unknown"


async def fetch_price_coingecko(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> PriceData:
    """Fetch current BTC price and change percentages from CoinGecko.

    Returns:
        PriceData with current price and 1h/24h/7d change percentages.

    Raises:
        SignalFetchError: If the request fails or returns unexpected data.
    """
    url = (base_url or settings.coingecko_api_url) + "/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_1hr_change": "true",
        "include_7d_change": "true",
    }
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=request_timeout)
        else:
            response = await client.get(url, params=params, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()
        btc = data["bitcoin"]

        return PriceData(
            price_usd=float(btc["usd"]),
            price_1h_change_pct=_safe_float(btc.get("usd_1h_change_percentage")),
            price_24h_change_pct=_safe_float(btc.get("usd_24h_change_percentage")),
            price_7d_change_pct=_safe_float(btc.get("usd_7d_change_percentage")),
            source="coingecko",
        )
    except httpx.HTTPStatusError as e:
        raise SignalFetchError("coingecko", f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError("coingecko", f"Request failed: {e}") from e
    except (KeyError, ValueError, TypeError) as e:
        raise SignalFetchError("coingecko", f"Unexpected response format: {e}") from e


async def fetch_price_binance(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> PriceData:
    """Fetch current BTC price from Binance (fallback source).

    Note: Binance ticker only provides 24h change, not 1h or 7d.

    Returns:
        PriceData with current price and 24h change percentage.

    Raises:
        SignalFetchError: If the request fails or returns unexpected data.
    """
    url = (base_url or settings.binance_api_url) + "/ticker/24hr"
    params = {"symbol": "BTCUSDT"}
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=request_timeout)
        else:
            response = await client.get(url, params=params, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()

        return PriceData(
            price_usd=float(data["lastPrice"]),
            price_24h_change_pct=float(data["priceChangePercent"]),
            source="binance",
        )
    except httpx.HTTPStatusError as e:
        raise SignalFetchError("binance", f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError("binance", f"Request failed: {e}") from e
    except (KeyError, ValueError, TypeError) as e:
        raise SignalFetchError("binance", f"Unexpected response format: {e}") from e


async def fetch_price_history_coingecko(
    days: int = 30,
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> PriceHistory:
    """Fetch historical BTC prices from CoinGecko for moving averages.

    Args:
        days: Number of days of history to fetch (default 30).

    Returns:
        PriceHistory with (timestamp_ms, price_usd) tuples.

    Raises:
        SignalFetchError: If the request fails or returns unexpected data.
    """
    url = (base_url or settings.coingecko_api_url) + "/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": str(days)}
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=request_timeout)
        else:
            response = await client.get(url, params=params, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()

        prices = tuple(
            (float(point[0]), float(point[1])) for point in data["prices"]
        )

        return PriceHistory(prices=prices, source="coingecko")
    except httpx.HTTPStatusError as e:
        raise SignalFetchError("coingecko", f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError("coingecko", f"Request failed: {e}") from e
    except (KeyError, ValueError, TypeError, IndexError) as e:
        raise SignalFetchError("coingecko", f"Unexpected response format: {e}") from e


def _safe_float(value: object) -> float | None:
    """Convert a value to float, returning None if not possible."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None
