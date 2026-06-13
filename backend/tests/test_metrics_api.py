"""Tests for Bitcoin metrics API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.signals.bitcoin_card import BitcoinCardSummary, BmriComparison
from app.signals.exceptions import SignalFetchError

client = TestClient(app)


def _summary() -> BitcoinCardSummary:
    return BitcoinCardSummary(
        fetched_at="2026-06-12T10:00:00Z",
        price_usd=65000.0,
        price_sources={"coinbase": 65001.0, "kraken": 64999.0, "agreement": True},
        fastest_fee=18.0,
        half_hour_fee=12.0,
        hour_fee=8.0,
        minimum_fee=1.0,
        block_height=840000,
        hashrate=600_000_000_000_000_000_000.0,
        difficulty=83_000_000_000_000.0,
        unmined_btc=1_312_500.0,
        next_halving_eta="2028-04-20T00:00:00Z",
        source_names=("Coinbase", "Kraken", "mempool.space"),
        caveats=("Price and block height are cross-source checked.",),
        raw={"sample": "summary"},
    )


def _bmri() -> BmriComparison:
    return BmriComparison(
        fetched_at="2026-06-12T10:00:00Z",
        full_index=9.4,
        lite_index=11.2,
        difference=1.8,
        full_anchors={"realisedPrice": 43000.0},
        lite_components={"dma200Percentile": 8.0},
        stats={"recentMeanAbsoluteError": 2.1},
        history=(
            {"date": "2026-06-10", "fullIndex": 10.2, "liteIndex": 12.0},
            {"date": "2026-06-11", "fullIndex": 9.8, "liteIndex": 11.7},
        ),
        source_note="Full BMRI is parsed from public Checkonchain chart data.",
        raw={"sample": "bmri"},
    )


@patch("app.api.metrics.fetch_summary", new_callable=AsyncMock)
def test_metrics_summary_returns_normalized_payload(mock_fetch: AsyncMock) -> None:
    """GET /api/metrics/summary returns normalized Bitcoin Card summary fields."""
    mock_fetch.return_value = _summary()

    response = client.get("/api/metrics/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["fetched_at"] == "2026-06-12T10:00:00Z"
    assert data["price_usd"] == 65000.0
    assert data["price_sources"]["agreement"] is True
    assert data["fees"]["fastest_fee"] == 18.0
    assert data["fees"]["hour_fee"] == 8.0
    assert data["fees"]["minimum_fee"] == 1.0
    assert data["network"]["block_height"] == 840000
    assert data["network"]["unmined_btc"] == 1_312_500.0
    assert data["source_names"] == ["Coinbase", "Kraken", "mempool.space"]
    assert data["caveats"] == ["Price and block height are cross-source checked."]


@patch("app.api.metrics.fetch_bmri_comparison", new_callable=AsyncMock)
def test_metrics_bmri_returns_normalized_payload(mock_fetch: AsyncMock) -> None:
    """GET /api/metrics/bmri returns normalized BMRI fields, caveats, and history."""
    mock_fetch.return_value = _bmri()

    response = client.get("/api/metrics/bmri")

    assert response.status_code == 200
    data = response.json()
    assert data["fetched_at"] == "2026-06-12T10:00:00Z"
    assert data["full_index"] == 9.4
    assert data["lite_index"] == 11.2
    assert data["difference"] == 1.8
    assert data["full_anchors"]["realisedPrice"] == 43000.0
    assert data["lite_components"]["dma200Percentile"] == 8.0
    assert data["stats"]["recentMeanAbsoluteError"] == 2.1
    assert len(data["history"]) == 2
    assert data["history"][0]["date"] == "2026-06-10"
    assert data["source_note"].startswith("Full BMRI")


@patch("app.api.metrics.fetch_summary", new_callable=AsyncMock)
def test_metrics_summary_returns_502_when_bitcoin_card_unavailable(
    mock_fetch: AsyncMock,
) -> None:
    """GET /api/metrics/summary maps Bitcoin Card failures to 502."""
    mock_fetch.side_effect = SignalFetchError("bitcoin-card", "HTTP 503")

    response = client.get("/api/metrics/summary")

    assert response.status_code == 502
    assert response.json()["detail"] == "Bitcoin Card metrics unavailable"


@patch("app.api.metrics.fetch_bmri_comparison", new_callable=AsyncMock)
def test_metrics_bmri_returns_502_when_bitcoin_card_unavailable(
    mock_fetch: AsyncMock,
) -> None:
    """GET /api/metrics/bmri maps Bitcoin Card failures to 502."""
    mock_fetch.side_effect = SignalFetchError("bitcoin-card", "Unexpected response format")

    response = client.get("/api/metrics/bmri")

    assert response.status_code == 502
    assert response.json()["detail"] == "Bitcoin Card metrics unavailable"
