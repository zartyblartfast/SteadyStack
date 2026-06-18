"""Tests for fee endpoints backed by Bitcoin Card."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.signals.bitcoin_card import FeeHistoryBands, FeeProfile
from app.signals.exceptions import SignalFetchError

client = TestClient(app)


def _fee_history() -> FeeHistoryBands:
    return FeeHistoryBands(
        range="1w",
        points=(
            {
                "t": "2026-06-12T00:00:00Z",
                "minFee": 1,
                "p10Fee": 2,
                "p25Fee": 3,
                "medianFee": 5,
                "p75Fee": 8,
                "p90Fee": 12,
                "maxFee": 20,
            },
        ),
        source="mempool.space",
        source_quality="public-api-fee-rate-bands",
        partial=False,
        note=None,
        fetched_at="2026-06-12T10:00:00Z",
        raw={"sample": "fee-history"},
    )


def _fee_profile() -> FeeProfile:
    return FeeProfile(
        cadence="weekly",
        buy_amount_usd=100.0,
        target_vbytes=140,
        recommended_sat_vb=2.0,
        estimated_fee_usd=0.18,
        estimated_fee_pct_of_buy=0.18,
        confidence=0.82,
        regime="quiet",
        reason="2 sat/vB is realistic for a patient weekly DCA campaign.",
        current_fees={"fastestFee": 5, "halfHourFee": 4, "hourFee": 3, "minimumFee": 1},
        history_summary={
            "range": "1w",
            "p10Fee": 2,
            "medianFee": 5,
            "p90Fee": 12,
            "partial": False,
        },
        source="mempool.space",
        source_quality="public-api-fee-rate-bands",
        limitations="Fee targets are probabilistic estimates, not guarantees.",
        fetched_at="2026-06-12T10:00:00Z",
        raw={"sample": "fee-profile"},
    )


@patch("app.api.fees.fetch_fee_history_bands", new_callable=AsyncMock)
def test_fee_history_uses_bitcoin_card_and_returns_legacy_shape(
    mock_fetch: AsyncMock,
) -> None:
    """GET /api/fees/history/{period} maps Bitcoin Card fee bands to legacy chart fields."""
    mock_fetch.return_value = _fee_history()

    response = client.get("/api/fees/history/1w")

    assert response.status_code == 200
    data = response.json()
    assert data == [
        {
            "timestamp": 1781222400,
            "avgFee_0": 1.0,
            "avgFee_10": 2.0,
            "avgFee_25": 3.0,
            "avgFee_50": 5.0,
            "avgFee_75": 8.0,
            "avgFee_90": 12.0,
            "avgFee_100": 20.0,
        }
    ]
    mock_fetch.assert_awaited_once_with("1w")


@patch("app.api.fees.fetch_fee_history_bands", new_callable=AsyncMock)
def test_fee_history_maps_bitcoin_card_failure_to_502(mock_fetch: AsyncMock) -> None:
    """Bitcoin Card fee-history failures surface as safe 502 responses."""
    mock_fetch.side_effect = SignalFetchError("bitcoin-card", "HTTP 503")

    response = client.get("/api/fees/history/1w")

    assert response.status_code == 502
    assert response.json()["detail"] == "Bitcoin Card fee history unavailable"


def test_fee_history_rejects_invalid_period() -> None:
    response = client.get("/api/fees/history/10y")

    assert response.status_code == 400
    assert "Invalid period" in response.json()["detail"]


@patch("app.api.fees.fetch_fee_profile", new_callable=AsyncMock)
def test_fee_profile_returns_bitcoin_card_recommendation(mock_fetch: AsyncMock) -> None:
    """GET /api/fees/profile returns Bitcoin Card fee recommendation context."""
    mock_fetch.return_value = _fee_profile()

    response = client.get("/api/fees/profile?cadence=weekly&buyAmountUsd=100&targetVbytes=140")

    assert response.status_code == 200
    data = response.json()
    assert data["recommended_sat_vb"] == 2.0
    assert data["estimated_fee_usd"] == 0.18
    assert data["estimated_fee_pct_of_buy"] == 0.18
    assert data["confidence"] == 0.82
    assert data["regime"] == "quiet"
    assert data["reason"].startswith("2 sat/vB")
    mock_fetch.assert_awaited_once_with(
        cadence="weekly", buy_amount_usd=100.0, target_vbytes=140
    )


@patch("app.api.fees.fetch_fee_profile", new_callable=AsyncMock)
def test_fee_profile_maps_bitcoin_card_failure_to_502(mock_fetch: AsyncMock) -> None:
    mock_fetch.side_effect = SignalFetchError("bitcoin-card", "HTTP 503")

    response = client.get("/api/fees/profile?cadence=weekly&buyAmountUsd=100")

    assert response.status_code == 502
    assert response.json()["detail"] == "Bitcoin Card fee profile unavailable"
