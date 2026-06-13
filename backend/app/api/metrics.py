"""Bitcoin metrics API endpoints backed by Bitcoin Card."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.signals.bitcoin_card import fetch_bmri_comparison, fetch_summary
from app.signals.exceptions import SignalFetchError

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class FeeTiersResponse(BaseModel):
    fastest_fee: float
    half_hour_fee: float
    hour_fee: float
    minimum_fee: float


class NetworkSummaryResponse(BaseModel):
    block_height: int | None
    hashrate: float | None
    difficulty: float | None
    unmined_btc: float | None
    next_halving_eta: str | None


class MetricsSummaryResponse(BaseModel):
    fetched_at: str | None
    price_usd: float
    price_sources: dict[str, Any]
    fees: FeeTiersResponse
    network: NetworkSummaryResponse
    source_names: list[str]
    caveats: list[str]


class BmriResponse(BaseModel):
    fetched_at: str | None
    full_index: float
    lite_index: float
    difference: float | None
    full_anchors: dict[str, Any]
    lite_components: dict[str, Any]
    stats: dict[str, Any]
    history: list[dict[str, Any]]
    source_note: str | None


@router.get("/summary", response_model=MetricsSummaryResponse)
async def metrics_summary() -> MetricsSummaryResponse:
    """Return normalized Bitcoin metrics from Bitcoin Card."""
    try:
        summary = await fetch_summary()
    except SignalFetchError as e:
        raise HTTPException(status_code=502, detail="Bitcoin Card metrics unavailable") from e

    return MetricsSummaryResponse(
        fetched_at=summary.fetched_at,
        price_usd=summary.price_usd,
        price_sources=summary.price_sources,
        fees=FeeTiersResponse(
            fastest_fee=summary.fastest_fee,
            half_hour_fee=summary.half_hour_fee,
            hour_fee=summary.hour_fee,
            minimum_fee=summary.minimum_fee,
        ),
        network=NetworkSummaryResponse(
            block_height=summary.block_height,
            hashrate=summary.hashrate,
            difficulty=summary.difficulty,
            unmined_btc=summary.unmined_btc,
            next_halving_eta=summary.next_halving_eta,
        ),
        source_names=list(summary.source_names),
        caveats=list(summary.caveats),
    )


@router.get("/bmri", response_model=BmriResponse)
async def metrics_bmri() -> BmriResponse:
    """Return normalized BMRI comparison data from Bitcoin Card."""
    try:
        bmri = await fetch_bmri_comparison()
    except SignalFetchError as e:
        raise HTTPException(status_code=502, detail="Bitcoin Card metrics unavailable") from e

    return BmriResponse(
        fetched_at=bmri.fetched_at,
        full_index=bmri.full_index,
        lite_index=bmri.lite_index,
        difference=bmri.difference,
        full_anchors=bmri.full_anchors,
        lite_components=bmri.lite_components,
        stats=bmri.stats,
        history=list(bmri.history),
        source_note=bmri.source_note,
    )
