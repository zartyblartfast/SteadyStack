"""mempool.space API client — fee estimates and mempool congestion."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import settings
from app.signals.exceptions import SignalFetchError

logger = logging.getLogger(__name__)

FEES_ENDPOINT = "/v1/fees/recommended"
MEMPOOL_ENDPOINT = "/mempool"


@dataclass(frozen=True)
class FeeEstimates:
    """Fee rate estimates from mempool.space."""

    fastest_fee: float
    half_hour_fee: float
    hour_fee: float
    economy_fee: float
    minimum_fee: float


@dataclass(frozen=True)
class MempoolInfo:
    """Mempool size and congestion data."""

    size_bytes: int
    count: int

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)


async def fetch_fee_estimates(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> FeeEstimates:
    """Fetch recommended fee rates from mempool.space.

    Args:
        client: Optional pre-configured HTTP client (for testing).
        base_url: Override the API base URL.
        timeout: Request timeout in seconds.

    Returns:
        FeeEstimates with current fee rate recommendations.

    Raises:
        SignalFetchError: If the request fails or returns unexpected data.
    """
    url = (base_url or settings.mempool_api_url) + FEES_ENDPOINT
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=request_timeout)
        else:
            response = await client.get(url, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()

        return FeeEstimates(
            fastest_fee=float(data["fastestFee"]),
            half_hour_fee=float(data["halfHourFee"]),
            hour_fee=float(data["hourFee"]),
            economy_fee=float(data["economyFee"]),
            minimum_fee=float(data["minimumFee"]),
        )
    except httpx.HTTPStatusError as e:
        raise SignalFetchError("mempool.space", f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError("mempool.space", f"Request failed: {e}") from e
    except (KeyError, ValueError, TypeError) as e:
        raise SignalFetchError("mempool.space", f"Unexpected response format: {e}") from e


async def fetch_mempool_info(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> MempoolInfo:
    """Fetch mempool size and transaction count.

    Args:
        client: Optional pre-configured HTTP client (for testing).
        base_url: Override the API base URL.
        timeout: Request timeout in seconds.

    Returns:
        MempoolInfo with current mempool state.

    Raises:
        SignalFetchError: If the request fails or returns unexpected data.
    """
    url = (base_url or settings.mempool_api_url) + MEMPOOL_ENDPOINT
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=request_timeout)
        else:
            response = await client.get(url, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()

        return MempoolInfo(
            size_bytes=int(data["vsize"]),
            count=int(data["count"]),
        )
    except httpx.HTTPStatusError as e:
        raise SignalFetchError("mempool.space", f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError("mempool.space", f"Request failed: {e}") from e
    except (KeyError, ValueError, TypeError) as e:
        raise SignalFetchError("mempool.space", f"Unexpected response format: {e}") from e
