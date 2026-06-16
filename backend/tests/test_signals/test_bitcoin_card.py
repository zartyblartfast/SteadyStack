"""Tests for Bitcoin Card metrics adapter."""

from __future__ import annotations

import httpx
import pytest

from app.signals.bitcoin_card import fetch_bitcoin_risk, fetch_bmri_comparison, fetch_summary
from app.signals.exceptions import SignalFetchError

SAMPLE_SUMMARY = {
    "fetchedAt": "2026-06-12T10:00:00Z",
    "price": {
        "usd": 65000.0,
        "sources": {
            "coinbase": 65001.0,
            "kraken": 64999.0,
            "agreement": True,
        },
    },
    "fees": {
        "fastestFee": 18,
        "halfHourFee": 12,
        "hourFee": 8,
        "minimumFee": 1,
    },
    "network": {
        "blockHeight": 840000,
        "hashrate": 600_000_000_000_000_000_000,
        "difficulty": 83_000_000_000_000,
        "unminedBtc": 1_312_500.0,
        "nextHalvingEta": "2028-04-20T00:00:00Z",
    },
    "source": {
        "names": ["Coinbase", "Kraken", "mempool.space"],
        "caveats": ["Price and block height are cross-source checked."],
    },
}


SAMPLE_BMRI = {
    "fetchedAt": "2026-06-12T10:00:00Z",
    "latest": {
        "fullIndex": 9.4,
        "liteIndex": 11.2,
        "difference": 1.8,
        "fullAnchors": {
            "realisedPrice": 43000.0,
            "trueMarketMean": 50000.0,
        },
        "liteComponents": {
            "dma200Percentile": 8.0,
            "wma200Percentile": 12.0,
            "realizedPricePercentile": 13.6,
        },
    },
    "stats": {
        "recentMeanAbsoluteError": 2.1,
        "allHistoryMeanAbsoluteError": 4.4,
    },
    "history": [
        {"date": "2026-06-10", "fullIndex": 10.2, "liteIndex": 12.0},
        {"date": "2026-06-11", "fullIndex": 9.8, "liteIndex": 11.7},
    ],
    "source": {
        "note": "Full BMRI is parsed from public Checkonchain chart data, not an official API."
    },
}


SAMPLE_BITCOIN_RISK = {
    "metric": "bitcoin-risk-composite",
    "riskScore": 18.5,
    "band": "value",
    "mvrvZScore": 0.72,
    "mvrv": 1.43,
    "components": {
        "mvrvZDerived": {
            "value": 0.72,
            "score": 16.0,
            "sourceMetric": "CapMVRVCur/CapMrktCurUSD",
            "methodology": "Derived from Coin Metrics MVRV and market cap history.",
        },
        "puellIssuance": {
            "value": 0.61,
            "score": 12.0,
            "sourceMetric": "IssTotUSD",
            "methodology": "IssTotUSD / 365d moving average(IssTotUSD).",
        },
        "mayerMultiple": {
            "value": 0.92,
            "score": 24.0,
            "sourceMetric": "PriceUSD",
            "methodology": "PriceUSD / 200d SMA(PriceUSD).",
        },
        "ma200wDistance": {
            "value": 1.10,
            "score": 22.0,
            "sourceMetric": "PriceUSD",
            "methodology": "PriceUSD / 1400d SMA(PriceUSD).",
        },
    },
    "history": [
        {
            "date": "2026-06-10",
            "unixTs": 1781049600,
            "mvrv": 1.41,
            "mvrvZScore": 0.69,
            "components": {"mvrvZDerived": {"score": 15.0}},
            "riskScore": 17.0,
            "band": "value",
        },
        {
            "date": "2026-06-11",
            "unixTs": 1781136000,
            "mvrv": 1.43,
            "mvrvZScore": 0.72,
            "components": {"mvrvZDerived": {"score": 16.0}},
            "riskScore": 18.5,
            "band": "value",
        },
    ],
    "sentiment": {
        "metric": "crypto-fear-and-greed",
        "value": 32,
        "classification": "Fear",
        "dataDate": "2026-06-11",
        "unixTs": 1781136000,
        "source": {
            "name": "Alternative.me",
            "url": "https://alternative.me/crypto/fear-and-greed-index/",
            "sourceQuality": "free-api-attribution-required",
        },
        "methodology": "Separate sentiment context, not valuation risk.",
        "limitations": "Black-box behavioral score; attribution required.",
    },
    "sentimentStatus": "available",
    "source": {
        "name": "Coin Metrics Community API",
        "url": "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics",
        "sourceQuality": "community-api-derived",
    },
    "methodology": "Average of normalized free-source component scores.",
    "limitations": "Not Cowen Risk, not Glassnode-equivalent, and not a trading signal.",
    "dataDate": "2026-06-11",
    "unixTs": 1781136000,
    "fetchedAt": "2026-06-12T10:00:00Z",
}


@pytest.mark.asyncio
async def test_fetch_summary_parses_compact_payload() -> None:
    """Parses Bitcoin Card /api/summary into stable internal fields."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_SUMMARY)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_summary(client=client, base_url="http://bitcoin-card")

    assert result.fetched_at == "2026-06-12T10:00:00Z"
    assert result.price_usd == 65000.0
    assert result.price_sources["agreement"] is True
    assert result.fastest_fee == 18.0
    assert result.half_hour_fee == 12.0
    assert result.hour_fee == 8.0
    assert result.minimum_fee == 1.0
    assert result.block_height == 840000
    assert result.unmined_btc == 1_312_500.0
    assert result.next_halving_eta == "2028-04-20T00:00:00Z"
    assert "mempool.space" in result.source_names
    assert result.raw == SAMPLE_SUMMARY


@pytest.mark.asyncio
async def test_fetch_bmri_comparison_parses_latest_and_history() -> None:
    """Parses Bitcoin Card /api/bmri-comparison without losing caveats/history."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=SAMPLE_BMRI))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_bmri_comparison(client=client, base_url="http://bitcoin-card")

    assert result.fetched_at == "2026-06-12T10:00:00Z"
    assert result.full_index == 9.4
    assert result.lite_index == 11.2
    assert result.difference == 1.8
    assert result.source_note.startswith("Full BMRI is parsed")
    assert result.full_anchors["realisedPrice"] == 43000.0
    assert result.lite_components["dma200Percentile"] == 8.0
    assert result.stats["recentMeanAbsoluteError"] == 2.1
    assert len(result.history) == 2
    assert result.history[0]["date"] == "2026-06-10"
    assert result.raw == SAMPLE_BMRI


@pytest.mark.asyncio
async def test_fetch_summary_raises_signal_fetch_error_on_http_error() -> None:
    """Wraps Bitcoin Card HTTP failures as SignalFetchError."""
    transport = httpx.MockTransport(lambda request: httpx.Response(503, text="down"))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="bitcoin-card"):
            await fetch_summary(client=client, base_url="http://bitcoin-card")


@pytest.mark.asyncio
async def test_fetch_bmri_comparison_raises_signal_fetch_error_on_malformed_payload() -> None:
    """Rejects malformed BMRI payloads instead of returning misleading None values."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"latest": {}}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="Unexpected response format"):
            await fetch_bmri_comparison(client=client, base_url="http://bitcoin-card")


@pytest.mark.asyncio
async def test_fetch_bmri_comparison_accepts_zero_percentile_values() -> None:
    """Treats 0.0 as a valid BMRI percentile value, not as a missing field."""
    payload = {
        **SAMPLE_BMRI,
        "latest": {
            **SAMPLE_BMRI["latest"],
            "fullIndex": 0.0,
            "liteIndex": 0.0,
            "difference": 0.0,
        },
    }
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_bmri_comparison(client=client, base_url="http://bitcoin-card")

    assert result.full_index == 0.0
    assert result.lite_index == 0.0
    assert result.difference == 0.0


@pytest.mark.asyncio
async def test_fetch_bitcoin_risk_parses_composite_payload() -> None:
    """Parses Bitcoin Card /api/bitcoin-risk while preserving components/history."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=SAMPLE_BITCOIN_RISK)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_bitcoin_risk(client=client, base_url="http://bitcoin-card")

    assert result.fetched_at == "2026-06-12T10:00:00Z"
    assert result.metric == "bitcoin-risk-composite"
    assert result.risk_score == 18.5
    assert result.band == "value"
    assert result.mvrv_z_score == 0.72
    assert result.components["mayerMultiple"]["score"] == 24.0
    assert len(result.history) == 2
    assert result.history[0]["components"]["mvrvZDerived"]["score"] == 15.0
    assert result.sentiment_status == "available"
    assert result.sentiment["source"]["sourceQuality"] == "free-api-attribution-required"
    assert result.source["sourceQuality"] == "community-api-derived"
    assert result.limitations.startswith("Not Cowen Risk")
    assert result.raw == SAMPLE_BITCOIN_RISK


@pytest.mark.asyncio
async def test_fetch_bitcoin_risk_accepts_zero_risk_score() -> None:
    """Treats 0.0 as a valid Bitcoin Risk score, not as a missing field."""
    payload = {**SAMPLE_BITCOIN_RISK, "riskScore": 0.0}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_bitcoin_risk(client=client, base_url="http://bitcoin-card")

    assert result.risk_score == 0.0


@pytest.mark.asyncio
async def test_fetch_bitcoin_risk_raises_signal_fetch_error_on_malformed_payload() -> None:
    """Rejects malformed Bitcoin Risk payloads rather than returning partial values."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"metric": "x"}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SignalFetchError, match="Unexpected response format"):
            await fetch_bitcoin_risk(client=client, base_url="http://bitcoin-card")
