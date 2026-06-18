"""Fee APIs backed by Bitcoin Card."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.signals.bitcoin_card import fetch_fee_history_bands, fetch_fee_profile
from app.signals.exceptions import SignalFetchError

router = APIRouter(prefix="/api/fees", tags=["fees"])

VALID_PERIODS = {"24h", "3d", "1w", "1m", "3m", "6m", "1y", "2y", "3y"}
VALID_CADENCES = {"daily", "weekly", "monthly"}


@router.get("/history/{period}")
async def fee_history(period: str) -> list[dict[str, Any]]:
    """Return Bitcoin Card fee-history bands in the legacy chart shape.

    This endpoint intentionally preserves the existing frontend contract while
    replacing the direct mempool.space dependency with Bitcoin Card.
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Valid: {', '.join(sorted(VALID_PERIODS))}",
        )

    try:
        history = await fetch_fee_history_bands(period)
    except SignalFetchError as e:
        raise HTTPException(status_code=502, detail="Bitcoin Card fee history unavailable") from e

    return [_legacy_fee_history_point(point) for point in history.points]


@router.get("/profile")
async def fee_profile(
    cadence: str = Query(..., description="DCA cadence: daily, weekly, or monthly"),
    buy_amount_usd: float = Query(..., alias="buyAmountUsd", gt=0),
    target_vbytes: int = Query(140, alias="targetVbytes", gt=0),
) -> dict[str, Any]:
    """Return Bitcoin Card's patient DCA fee recommendation."""
    if cadence not in VALID_CADENCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cadence '{cadence}'. Valid: {', '.join(sorted(VALID_CADENCES))}",
        )

    try:
        profile = await fetch_fee_profile(
            cadence=cadence,
            buy_amount_usd=buy_amount_usd,
            target_vbytes=target_vbytes,
        )
    except SignalFetchError as e:
        raise HTTPException(status_code=502, detail="Bitcoin Card fee profile unavailable") from e

    return {
        "cadence": profile.cadence,
        "buy_amount_usd": profile.buy_amount_usd,
        "target_vbytes": profile.target_vbytes,
        "recommended_sat_vb": profile.recommended_sat_vb,
        "estimated_fee_usd": profile.estimated_fee_usd,
        "estimated_fee_pct_of_buy": profile.estimated_fee_pct_of_buy,
        "confidence": profile.confidence,
        "regime": profile.regime,
        "reason": profile.reason,
        "current_fees": profile.current_fees,
        "history_summary": profile.history_summary,
        "source": profile.source,
        "source_quality": profile.source_quality,
        "limitations": profile.limitations,
        "fetched_at": profile.fetched_at,
    }


def _legacy_fee_history_point(point: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": _timestamp_seconds(str(point["t"])),
        "avgFee_0": float(point["minFee"]),
        "avgFee_10": float(point["p10Fee"]),
        "avgFee_25": float(point["p25Fee"]),
        "avgFee_50": float(point["medianFee"]),
        "avgFee_75": float(point["p75Fee"]),
        "avgFee_90": float(point["p90Fee"]),
        "avgFee_100": float(point["maxFee"]),
    }


def _timestamp_seconds(value: str) -> int:
    normalized = value.replace("Z", "+00:00")
    return int(datetime.fromisoformat(normalized).timestamp())
