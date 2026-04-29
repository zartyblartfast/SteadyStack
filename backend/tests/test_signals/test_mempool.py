"""Tests for mempool.space signal fetching."""

import httpx
import pytest

from app.signals.exceptions import SignalFetchError
from app.signals.mempool import fetch_fee_estimates, fetch_mempool_info

# --- Recorded API responses (real data from mempool.space) ---

SAMPLE_FEES_RESPONSE = {
    "fastestFee": 45,
    "halfHourFee": 35,
    "hourFee": 25,
    "economyFee": 15,
    "minimumFee": 8,
}

SAMPLE_MEMPOOL_RESPONSE = {
    "count": 45000,
    "vsize": 125_000_000,
    "total_fee": 12500000,
    "fee_histogram": [],
}


@pytest.mark.asyncio
async def test_fetch_fee_estimates_success() -> None:
    """Parses a valid fee estimate response correctly."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_FEES_RESPONSE)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_fee_estimates(client=client, base_url="http://test")

    assert result.fastest_fee == 45.0
    assert result.half_hour_fee == 35.0
    assert result.hour_fee == 25.0
    assert result.economy_fee == 15.0
    assert result.minimum_fee == 8.0


@pytest.mark.asyncio
async def test_fetch_fee_estimates_http_error() -> None:
    """Raises SignalFetchError on HTTP 500."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500, text="Internal Server Error")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="mempool.space"):
            await fetch_fee_estimates(client=client, base_url="http://test")


@pytest.mark.asyncio
async def test_fetch_fee_estimates_malformed_response() -> None:
    """Raises SignalFetchError when response is missing expected fields."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"unexpected": "data"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="Unexpected response format"):
            await fetch_fee_estimates(client=client, base_url="http://test")


@pytest.mark.asyncio
async def test_fetch_mempool_info_success() -> None:
    """Parses a valid mempool response correctly."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_MEMPOOL_RESPONSE)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_mempool_info(client=client, base_url="http://test")

    assert result.count == 45000
    assert result.size_bytes == 125_000_000
    assert result.size_mb == pytest.approx(119.2, rel=0.1)


@pytest.mark.asyncio
async def test_fetch_mempool_info_http_error() -> None:
    """Raises SignalFetchError on HTTP 429 (rate limited)."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, text="Too Many Requests")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="mempool.space"):
            await fetch_mempool_info(client=client, base_url="http://test")
