"""Decision pipeline — orchestrates signals → policy → explanation.

This module is the top-level entry point for producing a decision.
It wires together the signal collector, policy evaluator, and explanation
generator. It contains no business logic of its own — only sequencing.
"""

from __future__ import annotations

import logging

from app.engine.explain import generate_explanation
from app.policy.evaluator import evaluate_policy
from app.policy.profiles import PRESETS, StrategyProfile
from app.schemas import Decision, SignalSnapshot
from app.signals.collector import collect_signals

logger = logging.getLogger(__name__)


async def run_pipeline(
    profile: StrategyProfile | None = None,
    profile_name: str = "balanced",
    snapshot: SignalSnapshot | None = None,
) -> Decision:
    """Run the full decision pipeline.

    Args:
        profile: Strategy profile to use. If None, looks up by profile_name.
        profile_name: Name of a preset profile (ignored if profile is provided).
        snapshot: Optional pre-built snapshot (for testing/backtesting).
            If None, collects live signals.

    Returns:
        A fully populated Decision with action, confidence, scores,
        reason, explanation, and the snapshot that produced it.
    """
    # Resolve profile
    if profile is None:
        profile = PRESETS.get(profile_name)
        if profile is None:
            raise ValueError(
                f"Unknown profile '{profile_name}'. "
                f"Available: {', '.join(PRESETS.keys())}"
            )

    # Collect signals (or use provided snapshot for backtesting)
    if snapshot is None:
        logger.info("Collecting live signals...")
        snapshot = await collect_signals()
        logger.info("Signals collected: price=%s, fees=%s, vol=%s",
                     snapshot.price_usd, snapshot.fee_rate_sat_vb, snapshot.volatility_24h_pct)
    else:
        logger.info("Using provided snapshot (backtest/test mode)")

    # Evaluate policy
    decision = evaluate_policy(snapshot, profile)
    logger.info("Policy result: action=%s, confidence=%.2f, score=%s",
                 decision.action.value, decision.confidence, decision.reason)

    # Generate explanation
    explanation = generate_explanation(decision)

    # Return decision with explanation attached
    return Decision(
        action=decision.action,
        amount_usd=decision.amount_usd,
        confidence=decision.confidence,
        scores=decision.scores,
        reason=decision.reason,
        explanation=explanation,
        snapshot=decision.snapshot,
        timestamp=decision.timestamp,
    )
