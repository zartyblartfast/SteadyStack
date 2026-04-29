"""Decision API endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engine.pipeline import run_pipeline
from app.policy.profiles import PRESETS
from app.schemas import SignalSnapshot

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


class RunPipelineRequest(BaseModel):
    """Request body for triggering a decision."""

    profile_name: str = Field(
        default="balanced",
        description="Strategy profile to use (conservative, balanced, aggressive)",
    )


class SignalScoreResponse(BaseModel):
    """A single signal score in the response."""

    name: str
    value: float
    weight: float
    reason: str


class DecisionResponse(BaseModel):
    """Response body for a decision."""

    action: str
    confidence: float
    reason: str
    explanation: str
    scores: list[SignalScoreResponse]
    snapshot_summary: dict[str, Any]


@router.post("/run", response_model=DecisionResponse)
async def run_decision(request: RunPipelineRequest) -> DecisionResponse:
    """Run the decision pipeline with live market data.

    This fetches current signals from all data sources, evaluates the
    policy rules, and returns a recommendation with full reasoning.
    """
    if request.profile_name not in PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown profile '{request.profile_name}'. "
            f"Available: {', '.join(PRESETS.keys())}",
        )

    decision = await run_pipeline(profile_name=request.profile_name)

    snapshot_summary: dict[str, Any] = {}
    if decision.snapshot is not None:
        snapshot_summary = {
            "price_usd": decision.snapshot.price_usd,
            "fee_rate_sat_vb": decision.snapshot.fee_rate_sat_vb,
            "volatility_24h_pct": decision.snapshot.volatility_24h_pct,
            "price_7d_avg": decision.snapshot.price_7d_avg,
            "mempool_depth_mb": decision.snapshot.mempool_depth_mb,
        }

    return DecisionResponse(
        action=decision.action.value,
        confidence=decision.confidence,
        reason=decision.reason,
        explanation=decision.explanation,
        scores=[
            SignalScoreResponse(
                name=s.name, value=s.value, weight=s.weight, reason=s.reason
            )
            for s in decision.scores
        ],
        snapshot_summary=snapshot_summary,
    )


@router.get("/profiles")
async def list_profiles() -> dict[str, Any]:
    """List available strategy profiles with their configurations."""
    profiles = {}
    for name, profile in PRESETS.items():
        profiles[name] = {
            "fee_threshold_low": profile.fee_threshold_low,
            "fee_threshold_mid": profile.fee_threshold_mid,
            "fee_threshold_high": profile.fee_threshold_high,
            "price_dip_pct": profile.price_dip_pct,
            "price_premium_pct": profile.price_premium_pct,
            "volatility_low": profile.volatility_low,
            "volatility_high": profile.volatility_high,
            "weight_fee": profile.weight_fee,
            "weight_price": profile.weight_price,
            "weight_volatility": profile.weight_volatility,
            "buy_score_threshold": profile.buy_score_threshold,
            "skip_score_threshold": profile.skip_score_threshold,
        }
    return {"profiles": profiles}
