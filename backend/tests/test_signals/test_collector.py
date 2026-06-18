"""Tests for Bitcoin Card-backed signal collection."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.signals.bitcoin_card import BitcoinCardSummary, BmriComparison
from app.signals.collector import collect_signals


def _summary() -> BitcoinCardSummary:
    return BitcoinCardSummary(
        fetched_at="2026-06-12T10:00:00Z",
        price_usd=65000.0,
        price_sources={"agreement": "verified"},
        fastest_fee=5.0,
        half_hour_fee=4.0,
        hour_fee=3.0,
        minimum_fee=1.0,
        block_height=840000,
        hashrate=600.0,
        difficulty=83_000_000_000_000.0,
        unmined_btc=1_312_500.0,
        next_halving_eta="2028-04-20T00:00:00Z",
        source_names=("bitcoin-card",),
        caveats=(),
        raw={"sample": "summary"},
    )


def _bmri() -> BmriComparison:
    return BmriComparison(
        fetched_at="2026-06-12T10:00:00Z",
        full_index=20.0,
        lite_index=21.0,
        difference=1.0,
        full_anchors={},
        lite_components={},
        stats={},
        history=(
            {"date": "2026-06-05", "price": 62000.0},
            {"date": "2026-06-06", "price": 62500.0},
            {"date": "2026-06-07", "price": 63000.0},
            {"date": "2026-06-08", "price": 63500.0},
            {"date": "2026-06-09", "price": 64000.0},
            {"date": "2026-06-10", "price": 64500.0},
            {"date": "2026-06-11", "price": 65000.0},
        ),
        source_note=None,
        raw={"sample": "bmri"},
    )


@pytest.mark.asyncio
@patch("app.signals.collector.fetch_bmri_comparison", new_callable=AsyncMock)
@patch("app.signals.collector.fetch_summary", new_callable=AsyncMock)
async def test_collect_signals_uses_bitcoin_card_summary_and_bmri_history(
    mock_summary: AsyncMock,
    mock_bmri: AsyncMock,
) -> None:
    """Live signal collection should use Bitcoin Card, not legacy direct sources."""
    mock_summary.return_value = _summary()
    mock_bmri.return_value = _bmri()

    snapshot = await collect_signals()

    assert snapshot.price_usd == 65000.0
    assert snapshot.fee_rate_sat_vb == 3.0
    assert snapshot.fastest_fee == 5.0
    assert snapshot.half_hour_fee == 4.0
    assert snapshot.hour_fee == 3.0
    assert snapshot.economy_fee == 1.0
    assert snapshot.price_7d_avg is not None
    assert snapshot.volatility_7d_pct is not None
    mock_summary.assert_awaited_once()
    mock_bmri.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.signals.collector.fetch_bmri_comparison", new_callable=AsyncMock)
@patch("app.signals.collector.fetch_summary", new_callable=AsyncMock)
async def test_collect_signals_degrades_safely_when_bmri_history_unavailable(
    mock_summary: AsyncMock,
    mock_bmri: AsyncMock,
) -> None:
    """Current price/fees should still work if BMRI history cannot be fetched."""
    mock_summary.return_value = _summary()
    mock_bmri.side_effect = RuntimeError("BMRI unavailable")

    snapshot = await collect_signals()

    assert snapshot.price_usd == 65000.0
    assert snapshot.hour_fee == 3.0
    assert snapshot.price_7d_avg is None
    assert snapshot.volatility_7d_pct is None
