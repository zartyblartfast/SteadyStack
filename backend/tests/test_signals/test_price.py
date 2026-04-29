"""Tests for price signal fetching — CoinGecko and Binance."""

import httpx
import pytest

from app.signals.exceptions import SignalFetchError
from app.signals.price import (
    fetch_price_binance,
    fetch_price_coingecko,
    fetch_price_history_coingecko,
)

# --- Recorded API responses (real structure from CoinGecko / Binance) ---

SAMPLE_COINGECKO_PRICE = {
    "bitcoin": {
        "usd": 67500.0,
        "usd_1h_change_percentage": -0.35,
        "usd_24h_change_percentage": 2.1,
        "usd_7d_change_percentage": -1.8,
    }
}

SAMPLE_BINANCE_TICKER = {
    "symbol": "BTCUSDT",
    "lastPrice": "67450.00",
    "priceChangePercent": "1.95",
    "volume": "12345.678",
}

SAMPLE_COINGECKO_HISTORY = {
    "prices": [
        [1700000000000, 42000.0],
        [1700003600000, 42100.0],
        [1700007200000, 41900.0],
        [1700010800000, 42200.0],
        [1700014400000, 42050.0],
    ]
}


@pytest.mark.asyncio
async def test_fetch_price_coingecko_success() -> None:
    """Parses a valid CoinGecko price response."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_COINGECKO_PRICE)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_price_coingecko(client=client, base_url="http://test")

    assert result.price_usd == 67500.0
    assert result.price_1h_change_pct == pytest.approx(-0.35)
    assert result.price_24h_change_pct == pytest.approx(2.1)
    assert result.price_7d_change_pct == pytest.approx(-1.8)
    assert result.source == "coingecko"


@pytest.mark.asyncio
async def test_fetch_price_coingecko_missing_optional_fields() -> None:
    """Handles missing optional change percentages gracefully."""
    partial_response = {"bitcoin": {"usd": 67500.0}}
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=partial_response)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_price_coingecko(client=client, base_url="http://test")

    assert result.price_usd == 67500.0
    assert result.price_1h_change_pct is None
    assert result.price_24h_change_pct is None
    assert result.price_7d_change_pct is None


@pytest.mark.asyncio
async def test_fetch_price_coingecko_rate_limited() -> None:
    """Raises SignalFetchError on HTTP 429."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, text="Rate limit exceeded")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="coingecko"):
            await fetch_price_coingecko(client=client, base_url="http://test")


@pytest.mark.asyncio
async def test_fetch_price_binance_success() -> None:
    """Parses a valid Binance ticker response."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_BINANCE_TICKER)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_price_binance(client=client, base_url="http://test")

    assert result.price_usd == 67450.0
    assert result.price_24h_change_pct == pytest.approx(1.95)
    assert result.price_1h_change_pct is None  # Binance doesn't provide 1h
    assert result.source == "binance"


@pytest.mark.asyncio
async def test_fetch_price_binance_http_error() -> None:
    """Raises SignalFetchError on Binance HTTP error."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(503, text="Service Unavailable")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="binance"):
            await fetch_price_binance(client=client, base_url="http://test")


@pytest.mark.asyncio
async def test_fetch_price_history_success() -> None:
    """Parses a valid CoinGecko market chart response."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_COINGECKO_HISTORY)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_price_history_coingecko(
            days=7, client=client, base_url="http://test"
        )

    assert len(result.prices) == 5
    assert result.prices[0] == (1700000000000.0, 42000.0)
    assert result.source == "coingecko"


@pytest.mark.asyncio
async def test_fetch_price_history_empty() -> None:
    """Handles an empty prices array."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"prices": []})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_price_history_coingecko(
            days=7, client=client, base_url="http://test"
        )

    assert len(result.prices) == 0
