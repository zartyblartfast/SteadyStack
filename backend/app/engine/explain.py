"""Template-based explanation generator.

Produces human-readable explanations from Decision data. No LLM involved —
explanations are deterministic templates filled with actual values.

Pure function — no I/O, no side effects.
"""

from __future__ import annotations

from app.schemas import Action, Decision


def generate_explanation(decision: Decision) -> str:
    """Generate a human-readable explanation for a decision.

    Args:
        decision: The Decision from the policy evaluator.

    Returns:
        A multi-line explanation string suitable for Telegram or dashboard display.
    """
    snapshot = decision.snapshot

    if decision.action == Action.BUY:
        return _explain_buy(decision)
    elif decision.action == Action.SKIP:
        return _explain_skip(decision)
    else:
        return _explain_wait(decision)


def _explain_buy(decision: Decision) -> str:
    """Explain a BUY decision."""
    snapshot = decision.snapshot
    lines = [
        "✅ Recommendation: BUY",
        f"Confidence: {decision.confidence:.0%}",
        "",
    ]

    if snapshot is not None:
        if snapshot.price_usd is not None:
            lines.append(f"BTC Price: ${snapshot.price_usd:,.0f}")
        if snapshot.price_7d_avg is not None:
            lines.append(f"7-day Average: ${snapshot.price_7d_avg:,.0f}")
        if snapshot.fee_rate_sat_vb is not None:
            lines.append(f"Fee Rate: {snapshot.fee_rate_sat_vb:.0f} sat/vB")
        if snapshot.volatility_24h_pct is not None:
            lines.append(f"24h Volatility: {snapshot.volatility_24h_pct:.1f}%")
        lines.append("")

    lines.append("Why now:")
    for score in decision.scores:
        indicator = _score_indicator(score.value)
        lines.append(f"  {indicator} {score.reason}")

    return "\n".join(lines)


def _explain_skip(decision: Decision) -> str:
    """Explain a SKIP decision."""
    snapshot = decision.snapshot
    lines = [
        "⏭️ Recommendation: SKIP",
        f"Confidence: {decision.confidence:.0%}",
        "",
    ]

    if snapshot is not None:
        if snapshot.price_usd is not None:
            lines.append(f"BTC Price: ${snapshot.price_usd:,.0f}")
        if snapshot.fee_rate_sat_vb is not None:
            lines.append(f"Fee Rate: {snapshot.fee_rate_sat_vb:.0f} sat/vB")
        lines.append("")

    lines.append("Why not now:")
    for score in decision.scores:
        if score.value < 0.4:
            lines.append(f"  ⚠️ {score.reason}")
        else:
            lines.append(f"  ℹ️ {score.reason}")

    return "\n".join(lines)


def _explain_wait(decision: Decision) -> str:
    """Explain a WAIT decision."""
    snapshot = decision.snapshot
    lines = [
        "⏳ Recommendation: WAIT",
        f"Confidence: {decision.confidence:.0%}",
        "",
        "Conditions are mixed — holding off for now.",
        "",
    ]

    if snapshot is not None:
        if snapshot.price_usd is not None:
            lines.append(f"BTC Price: ${snapshot.price_usd:,.0f}")
        if snapshot.fee_rate_sat_vb is not None:
            lines.append(f"Fee Rate: {snapshot.fee_rate_sat_vb:.0f} sat/vB")
        lines.append("")

    lines.append("Signal breakdown:")
    for score in decision.scores:
        indicator = _score_indicator(score.value)
        lines.append(f"  {indicator} {score.reason}")

    lines.append("")
    lines.append("Will re-evaluate at the next check window.")

    return "\n".join(lines)


def _score_indicator(value: float) -> str:
    """Return a visual indicator for a score value."""
    if value >= 0.7:
        return "🟢"
    elif value >= 0.4:
        return "🟡"
    else:
        return "🔴"
