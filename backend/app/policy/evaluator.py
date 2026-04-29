"""Policy evaluator — combines signal scores into a final Decision.

This is the core of the decision engine. It takes a SignalSnapshot and a
StrategyProfile, scores each signal, combines the scores using weighted
averaging, applies staleness penalties, and returns a Decision.

Pure function — no I/O, no side effects, deterministic.
"""

from __future__ import annotations

from app.config import settings
from app.policy.profiles import StrategyProfile
from app.policy.scoring import score_fees, score_price, score_volatility
from app.schemas import Action, Decision, SignalScore, SignalSnapshot


def evaluate_policy(snapshot: SignalSnapshot, profile: StrategyProfile) -> Decision:
    """Evaluate market conditions and return a BUY / SKIP / WAIT decision.

    Args:
        snapshot: Current market data from the signals module.
        profile: Strategy configuration defining thresholds and weights.

    Returns:
        Decision with action, confidence, scores, and reasoning.
    """
    # Score each signal
    fee_score = score_fees(snapshot, profile)
    price_score = score_price(snapshot, profile)
    vol_score = score_volatility(snapshot, profile)
    scores = (fee_score, price_score, vol_score)

    # Weighted average
    total_weight = sum(s.weight for s in scores)
    if total_weight == 0:
        weighted_score = 0.0
    else:
        weighted_score = sum(s.value * s.weight for s in scores) / total_weight

    # Extreme negative signal penalty: when any signal is at its worst (0.0),
    # it should drag the overall score down hard. Without this, two good signals
    # can override one terrible signal — e.g., low volatility + price dip can
    # push through a buy despite 120 sat/vB fees, which is never correct.
    # Each extreme negative signal applies a penalty proportional to its weight.
    for s in scores:
        if s.value == 0.0:
            penalty = min((s.weight / total_weight) * 2.0, 1.0) if total_weight > 0 else 0.0
            weighted_score *= (1.0 - penalty)

    # Compute confidence (starts at weighted_score, reduced by staleness)
    confidence = _compute_confidence(weighted_score, snapshot)

    # Determine action
    action = _determine_action(weighted_score, confidence, profile)

    # Build reason summary
    reason = _build_reason(action, weighted_score, scores, profile)

    return Decision(
        action=action,
        confidence=confidence,
        scores=scores,
        reason=reason,
        snapshot=snapshot,
    )


def _compute_confidence(weighted_score: float, snapshot: SignalSnapshot) -> float:
    """Compute confidence from weighted score and data freshness.

    Confidence starts at the weighted score (how aligned the signals are)
    and is penalised for stale data. All-missing data results in confidence ≈ 0.
    """
    max_staleness_s = settings.max_data_staleness_minutes * 60

    # Count how many data categories are missing (all fields None)
    missing_count = 0
    if snapshot.fee_rate_sat_vb is None:
        missing_count += 1
    if snapshot.price_usd is None:
        missing_count += 1
    if snapshot.volatility_24h_pct is None:
        missing_count += 1

    # All data missing → near-zero confidence
    if missing_count == 3:
        return 0.0

    # Start with score-based confidence
    confidence = weighted_score

    # Staleness penalty — each stale source reduces confidence
    staleness_values = [
        snapshot.staleness_fees_s,
        snapshot.staleness_price_s,
        snapshot.staleness_onchain_s,
    ]
    for staleness_s in staleness_values:
        if staleness_s > 0 and max_staleness_s > 0:
            staleness_ratio = min(staleness_s / max_staleness_s, 1.0)
            # Each stale source can reduce confidence by up to 20%
            confidence *= 1.0 - (staleness_ratio * 0.2)

    # Missing data penalty (partial) — each missing source reduces by 15%
    confidence *= 1.0 - (missing_count * 0.15)

    return max(0.0, min(1.0, confidence))


def _determine_action(
    weighted_score: float, confidence: float, profile: StrategyProfile
) -> Action:
    """Map weighted score and confidence to an action.

    - Score >= buy_threshold AND confidence > 0 → BUY
    - Score < skip_threshold → SKIP
    - In between → WAIT
    - Zero confidence → always SKIP (safety rule)
    """
    if confidence == 0.0:
        return Action.SKIP

    if weighted_score >= profile.buy_score_threshold:
        return Action.BUY
    elif weighted_score < profile.skip_score_threshold:
        return Action.SKIP
    else:
        return Action.WAIT


def _build_reason(
    action: Action,
    weighted_score: float,
    scores: tuple[SignalScore, ...],
    profile: StrategyProfile,
) -> str:
    """Build a concise reason string from the decision components."""
    score_parts = [f"{s.name}={s.value:.2f}" for s in scores]
    scores_summary = ", ".join(score_parts)

    if action == Action.BUY:
        return (
            f"BUY — weighted score {weighted_score:.2f} ≥ {profile.buy_score_threshold:.2f} "
            f"threshold [{scores_summary}]"
        )
    elif action == Action.SKIP:
        return (
            f"SKIP — weighted score {weighted_score:.2f} < {profile.skip_score_threshold:.2f} "
            f"threshold [{scores_summary}]"
        )
    else:
        return (
            f"WAIT — weighted score {weighted_score:.2f} between "
            f"{profile.skip_score_threshold:.2f}–{profile.buy_score_threshold:.2f} "
            f"[{scores_summary}]"
        )
