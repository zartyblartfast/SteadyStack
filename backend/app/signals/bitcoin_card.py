"""Bitcoin Card API adapter.

Bitcoin Card exposes local Bitcoin metrics through HTTP endpoints. This module
normalizes those payloads into stable internal dataclasses so the rest of
SteadyStack does not depend on Bitcoin Card's raw response shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.signals.exceptions import SignalFetchError

SUMMARY_ENDPOINT = "/api/summary"
BMRI_COMPARISON_ENDPOINT = "/api/bmri-comparison"
SOURCE_NAME = "bitcoin-card"


@dataclass(frozen=True)
class BitcoinCardSummary:
    """Normalized compact Bitcoin metrics from Bitcoin Card /api/summary."""

    fetched_at: str | None
    price_usd: float
    price_sources: dict[str, Any]
    fastest_fee: float
    half_hour_fee: float
    hour_fee: float
    minimum_fee: float
    block_height: int | None
    hashrate: float | None
    difficulty: float | None
    unmined_btc: float | None
    next_halving_eta: str | None
    source_names: tuple[str, ...]
    caveats: tuple[str, ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class BmriComparison:
    """Normalized BMRI full/lite comparison from Bitcoin Card."""

    fetched_at: str | None
    full_index: float
    lite_index: float
    difference: float | None
    full_anchors: dict[str, Any]
    lite_components: dict[str, Any]
    stats: dict[str, Any]
    history: tuple[dict[str, Any], ...]
    source_note: str | None
    raw: dict[str, Any]


async def fetch_summary(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> BitcoinCardSummary:
    """Fetch and normalize Bitcoin Card /api/summary.

    Raises:
        SignalFetchError: If the request fails or the response is malformed.
    """
    data = await _get_json(
        endpoint=SUMMARY_ENDPOINT,
        client=client,
        base_url=base_url,
        timeout=timeout,
    )

    try:
        price = _dict(data["price"], "price")
        fees = _dict(data["fees"], "fees")
        network = _dict(data.get("network", {}), "network")
        source = _dict(data.get("source", {}), "source")

        return BitcoinCardSummary(
            fetched_at=_optional_str(_first_present(data, "fetchedAt", "fetched_at")),
            price_usd=_required_float(_first_present(price, "usd", "priceUsd"), "price.usd"),
            price_sources=_dict(price.get("sources", {}), "price.sources"),
            fastest_fee=_required_float(
                _first_present(fees, "fastestFee", "fastest_fee"), "fees.fastestFee"
            ),
            half_hour_fee=_required_float(
                _first_present(fees, "halfHourFee", "half_hour_fee"), "fees.halfHourFee"
            ),
            hour_fee=_required_float(_first_present(fees, "hourFee", "hour_fee"), "fees.hourFee"),
            minimum_fee=_required_float(
                _first_present(fees, "minimumFee", "minimum_fee"), "fees.minimumFee"
            ),
            block_height=_optional_int(
                _first_present(network, "blockHeight", "block_height"), "network.blockHeight"
            ),
            hashrate=_optional_float(network.get("hashrate"), "network.hashrate"),
            difficulty=_optional_float(network.get("difficulty"), "network.difficulty"),
            unmined_btc=_optional_float(
                _first_present(network, "unminedBtc", "unmined_btc"), "network.unminedBtc"
            ),
            next_halving_eta=_optional_str(
                _first_present(network, "nextHalvingEta", "next_halving_eta")
            ),
            source_names=_str_tuple(source.get("names", ())),
            caveats=_str_tuple(source.get("caveats", ())),
            raw=data,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise SignalFetchError(SOURCE_NAME, f"Unexpected response format: {e}") from e


async def fetch_bmri_comparison(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> BmriComparison:
    """Fetch and normalize Bitcoin Card /api/bmri-comparison.

    Raises:
        SignalFetchError: If the request fails or the response is malformed.
    """
    data = await _get_json(
        endpoint=BMRI_COMPARISON_ENDPOINT,
        client=client,
        base_url=base_url,
        timeout=timeout,
    )

    try:
        latest = _dict(data["latest"], "latest")
        source = _dict(data.get("source", {}), "source")
        history = data.get("history", ())
        if not isinstance(history, list | tuple):
            raise TypeError("history must be a list")

        return BmriComparison(
            fetched_at=_optional_str(_first_present(data, "fetchedAt", "fetched_at")),
            full_index=_required_float(
                _first_present(latest, "fullIndex", "full_index"), "latest.fullIndex"
            ),
            lite_index=_required_float(
                _first_present(latest, "liteIndex", "lite_index"), "latest.liteIndex"
            ),
            difference=_optional_float(
                latest.get("difference"), "latest.difference"
            ),
            full_anchors=_dict(
                _first_present(latest, "fullAnchors", "full_anchors") or {},
                "latest.fullAnchors",
            ),
            lite_components=_dict(
                _first_present(latest, "liteComponents", "lite_components") or {},
                "latest.liteComponents",
            ),
            stats=_dict(data.get("stats", {}), "stats"),
            history=tuple(_dict(item, "history item") for item in history),
            source_note=_optional_str(source.get("note")),
            raw=data,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise SignalFetchError(SOURCE_NAME, f"Unexpected response format: {e}") from e


async def _get_json(
    *,
    endpoint: str,
    client: httpx.AsyncClient | None,
    base_url: str | None,
    timeout: float | None,
) -> dict[str, Any]:
    url = _join_url(base_url or settings.bitcoin_card_base_url, endpoint)
    request_timeout = timeout or settings.http_timeout

    try:
        if client is None:
            async with httpx.AsyncClient() as owned_client:
                response = await owned_client.get(url, timeout=request_timeout)
        else:
            response = await client.get(url, timeout=request_timeout)

        response.raise_for_status()
        data = response.json()
        return _dict(data, "response")
    except httpx.HTTPStatusError as e:
        raise SignalFetchError(SOURCE_NAME, f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise SignalFetchError(SOURCE_NAME, f"Request failed: {e}") from e
    except (ValueError, TypeError) as e:
        raise SignalFetchError(SOURCE_NAME, f"Unexpected response format: {e}") from e


def _join_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + endpoint


def _dict(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be an object")
    return value


def _required_float(value: object, name: str) -> float:
    if value is None:
        raise KeyError(name)
    return float(value)  # type: ignore[arg-type]



def _first_present(data: dict[str, Any], *keys: str) -> object | None:
    """Return the first present key's value, preserving falsy values like 0.0."""
    for key in keys:
        if key in data:
            return data[key]
    return None

def _optional_float(value: object, name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be numeric") from e


def _optional_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be an integer") from e


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise TypeError("expected list of strings")
    return tuple(str(item) for item in value)
