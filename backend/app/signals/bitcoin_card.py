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
BITCOIN_RISK_ENDPOINT = "/api/bitcoin-risk"
FEE_HISTORY_ENDPOINT = "/api/fee-history"
FEE_PROFILE_ENDPOINT = "/api/fee-profile"
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
    full_anchors: dict[str, Any] | list[dict[str, Any]]
    lite_components: dict[str, Any]
    stats: dict[str, Any]
    history: tuple[dict[str, Any], ...]
    source_note: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class BitcoinRisk:
    """Normalized Bitcoin Risk composite from Bitcoin Card."""

    fetched_at: str | None
    metric: str
    risk_score: float
    band: str
    mvrv_z_score: float | None
    mvrv: float | None
    components: dict[str, Any]
    history: tuple[dict[str, Any], ...]
    sentiment: dict[str, Any] | None
    sentiment_status: str | None
    source: dict[str, Any]
    methodology: str | None
    limitations: str | None
    data_date: str | None
    unix_ts: int | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class FeeHistoryBands:
    """Normalized Bitcoin Card fee-history percentile bands."""

    range: str
    points: tuple[dict[str, Any], ...]
    source: str | None
    source_quality: str | None
    partial: bool
    note: str | None
    fetched_at: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class FeeProfile:
    """Normalized Bitcoin Card patient DCA fee recommendation."""

    cadence: str
    buy_amount_usd: float
    target_vbytes: int
    recommended_sat_vb: float
    estimated_fee_usd: float
    estimated_fee_pct_of_buy: float
    confidence: float
    regime: str
    reason: str
    current_fees: dict[str, Any]
    history_summary: dict[str, Any]
    source: str | None
    source_quality: str | None
    limitations: str | None
    fetched_at: str | None
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
        block_height = _dict(data.get("blockHeight", {}), "blockHeight")
        mining = _dict(data.get("mining", {}), "mining")
        supply = _dict(data.get("supply", {}), "supply")
        source = _dict(data.get("source", {}), "source")

        price_sources = price.get("sources", {})
        if isinstance(price_sources, list):
            price_sources = {"records": price_sources, "agreement": price.get("agreement")}

        source_names = source.get("names")
        if source_names is None:
            source_names = _source_names_from_summary(data)

        block_height_value = _first_present(network, "blockHeight", "block_height")
        if block_height_value is None:
            block_height_value = _first_present(block_height, "value")

        hashrate_value = _first_present(network, "hashrate", "hashrateEhS")
        if hashrate_value is None:
            hashrate_value = _first_present(mining, "hashrate", "hashrateEhS")

        difficulty_value = _first_present(network, "difficulty")
        if difficulty_value is None:
            difficulty_value = _first_present(mining, "difficulty")

        unmined_value = _first_present(network, "unminedBtc", "unmined_btc")
        if unmined_value is None:
            unmined_value = _first_present(supply, "unmined", "unminedBtc")

        halving_value = _first_present(network, "nextHalvingEta", "next_halving_eta")
        if halving_value is None:
            halving_value = _first_present(supply, "nextHalvingEta")

        return BitcoinCardSummary(
            fetched_at=_optional_str(
                _first_present(data, "fetchedAt", "fetched_at", "generatedAt")
            ),
            price_usd=_required_float(
                _first_present(price, "usd", "priceUsd", "value"), "price.usd"
            ),
            price_sources=_dict(price_sources, "price.sources"),
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
            block_height=_optional_int(block_height_value, "network.blockHeight"),
            hashrate=_optional_float(hashrate_value, "network.hashrate"),
            difficulty=_optional_float(difficulty_value, "network.difficulty"),
            unmined_btc=_optional_float(unmined_value, "network.unminedBtc"),
            next_halving_eta=_optional_str(halving_value),
            source_names=_str_tuple(source_names),
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
            full_anchors=_dict_or_list(
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


async def fetch_bitcoin_risk(
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> BitcoinRisk:
    """Fetch and normalize Bitcoin Card /api/bitcoin-risk.

    Raises:
        SignalFetchError: If the request fails or the response is malformed.
    """
    data = await _get_json(
        endpoint=BITCOIN_RISK_ENDPOINT,
        client=client,
        base_url=base_url,
        timeout=timeout,
    )

    try:
        history = data.get("history", ())
        if not isinstance(history, list | tuple):
            raise TypeError("history must be a list")

        sentiment = data.get("sentiment")
        if sentiment is not None:
            sentiment = _dict(sentiment, "sentiment")

        return BitcoinRisk(
            fetched_at=_optional_str(_first_present(data, "fetchedAt", "fetched_at")),
            metric=str(data["metric"]),
            risk_score=_required_float(
                _first_present(data, "riskScore", "risk_score"), "riskScore"
            ),
            band=str(data["band"]),
            mvrv_z_score=_optional_float(
                _first_present(data, "mvrvZScore", "mvrv_z_score"), "mvrvZScore"
            ),
            mvrv=_optional_float(data.get("mvrv"), "mvrv"),
            components=_dict(data.get("components", {}), "components"),
            history=tuple(_dict(item, "history item") for item in history),
            sentiment=sentiment,
            sentiment_status=_optional_str(
                _first_present(data, "sentimentStatus", "sentiment_status")
            ),
            source=_dict(data.get("source", {}), "source"),
            methodology=_optional_str(data.get("methodology")),
            limitations=_optional_str(data.get("limitations")),
            data_date=_optional_str(_first_present(data, "dataDate", "data_date")),
            unix_ts=_optional_int(_first_present(data, "unixTs", "unix_ts"), "unixTs"),
            raw=data,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise SignalFetchError(SOURCE_NAME, f"Unexpected response format: {e}") from e


async def fetch_fee_history_bands(
    range: str,
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> FeeHistoryBands:
    """Fetch and normalize Bitcoin Card /api/fee-history."""
    data = await _get_json(
        endpoint=f"{FEE_HISTORY_ENDPOINT}?range={range}",
        client=client,
        base_url=base_url,
        timeout=timeout,
    )

    try:
        points = data["points"]
        if not isinstance(points, list | tuple):
            raise TypeError("points must be a list")

        return FeeHistoryBands(
            range=str(data["range"]),
            points=tuple(_fee_history_point(item) for item in points),
            source=_optional_str(data.get("source")),
            source_quality=_optional_str(_first_present(data, "sourceQuality", "source_quality")),
            partial=bool(data.get("partial", False)),
            note=_optional_str(data.get("note")),
            fetched_at=_optional_str(_first_present(data, "fetchedAt", "fetched_at")),
            raw=data,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise SignalFetchError(SOURCE_NAME, f"Unexpected response format: {e}") from e


async def fetch_fee_profile(
    *,
    cadence: str,
    buy_amount_usd: float,
    target_vbytes: int = 140,
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> FeeProfile:
    """Fetch and normalize Bitcoin Card /api/fee-profile."""
    endpoint = (
        f"{FEE_PROFILE_ENDPOINT}?cadence={cadence}"
        f"&buyAmountUsd={buy_amount_usd}&targetVbytes={target_vbytes}"
    )
    data = await _get_json(endpoint=endpoint, client=client, base_url=base_url, timeout=timeout)

    try:
        return FeeProfile(
            cadence=str(data["cadence"]),
            buy_amount_usd=_required_float(
                _first_present(data, "buyAmountUsd", "buy_amount_usd"), "buyAmountUsd"
            ),
            target_vbytes=_required_int(
                _first_present(data, "targetVbytes", "target_vbytes"), "targetVbytes"
            ),
            recommended_sat_vb=_required_float(
                _first_present(data, "recommendedSatVb", "recommended_sat_vb"),
                "recommendedSatVb",
            ),
            estimated_fee_usd=_required_float(
                _first_present(data, "estimatedFeeUsd", "estimated_fee_usd"),
                "estimatedFeeUsd",
            ),
            estimated_fee_pct_of_buy=_required_float(
                _first_present(data, "estimatedFeePctOfBuy", "estimated_fee_pct_of_buy"),
                "estimatedFeePctOfBuy",
            ),
            confidence=_required_float(data.get("confidence"), "confidence"),
            regime=str(data["regime"]),
            reason=str(data["reason"]),
            current_fees=_dict(
                _first_present(data, "currentFees", "current_fees") or {}, "currentFees"
            ),
            history_summary=_dict(
                _first_present(data, "historySummary", "history_summary") or {},
                "historySummary",
            ),
            source=_optional_str(data.get("source")),
            source_quality=_optional_str(_first_present(data, "sourceQuality", "source_quality")),
            limitations=_optional_str(data.get("limitations")),
            fetched_at=_optional_str(_first_present(data, "fetchedAt", "fetched_at")),
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


def _source_names_from_summary(data: dict[str, Any]) -> tuple[str, ...]:
    names: list[str] = []
    for section_name in ("price", "blockHeight", "fees", "mining"):
        section = data.get(section_name)
        if isinstance(section, dict):
            source = section.get("source")
            if isinstance(source, str):
                names.append(source)
            sources = section.get("sources")
            if isinstance(sources, list):
                for item in sources:
                    if isinstance(item, dict) and isinstance(item.get("source"), str):
                        names.append(item["source"])
    return tuple(dict.fromkeys(names))


def _join_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + endpoint


def _dict(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be an object")
    return value


def _dict_or_list(value: object, name: str) -> dict[str, Any] | list[dict[str, Any]]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise TypeError(f"{name} must be an object or list of objects")


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

def _required_int(value: object, name: str) -> int:
    if value is None:
        raise KeyError(name)
    return int(value)  # type: ignore[arg-type]


def _fee_history_point(value: object) -> dict[str, Any]:
    point = _dict(value, "fee history point")
    return {
        "t": _optional_str(point.get("t")) or str(point["t"]),
        "minFee": _required_float(_first_present(point, "minFee", "min_fee"), "minFee"),
        "p10Fee": _required_float(_first_present(point, "p10Fee", "p10_fee"), "p10Fee"),
        "p25Fee": _required_float(_first_present(point, "p25Fee", "p25_fee"), "p25Fee"),
        "medianFee": _required_float(
            _first_present(point, "medianFee", "median_fee"), "medianFee"
        ),
        "p75Fee": _required_float(_first_present(point, "p75Fee", "p75_fee"), "p75Fee"),
        "p90Fee": _required_float(_first_present(point, "p90Fee", "p90_fee"), "p90Fee"),
        "maxFee": _required_float(_first_present(point, "maxFee", "max_fee"), "maxFee"),
    }


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
