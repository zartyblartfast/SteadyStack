"""Integration tests for the engine pipeline and explanation generator."""

from __future__ import annotations

import pytest

from app.engine.explain import generate_explanation
from app.engine.pipeline import run_pipeline
from app.policy.evaluator import evaluate_policy
from app.policy.profiles import BALANCED
from app.schemas import Action, Decision, SignalSnapshot


# --- Explanation tests ---

class TestExplanations:
    def test_buy_explanation_contains_key_info(self) -> None:
        """BUY explanation includes price, fees, and signal breakdown."""
        snapshot = SignalSnapshot(
            price_usd=65000.0,
            price_7d_avg=65200.0,
            fee_rate_sat_vb=12.0,
            volatility_24h_pct=1.2,
        )
        decision = evaluate_policy(snapshot, BALANCED)
        explanation = generate_explanation(decision)

        assert "BUY" in explanation
        assert "$65,000" in explanation
        assert "12 sat/vB" in explanation
        assert "Why now:" in explanation

    def test_skip_explanation_contains_warnings(self) -> None:
        """SKIP explanation highlights the negative signals."""
        snapshot = SignalSnapshot(
            price_usd=70000.0,
            price_7d_avg=65000.0,
            fee_rate_sat_vb=95.0,
            volatility_24h_pct=6.0,
        )
        decision = evaluate_policy(snapshot, BALANCED)
        explanation = generate_explanation(decision)

        assert "SKIP" in explanation
        assert "Why not now:" in explanation

    def test_wait_explanation_shows_mixed_signals(self) -> None:
        """WAIT explanation shows signal breakdown and re-evaluate message."""
        snapshot = SignalSnapshot(
            price_usd=64000.0,
            price_7d_avg=63800.0,
            fee_rate_sat_vb=30.0,
            volatility_24h_pct=6.5,
        )
        decision = evaluate_policy(snapshot, BALANCED)
        explanation = generate_explanation(decision)

        assert "WAIT" in explanation
        assert "Signal breakdown:" in explanation
        assert "re-evaluate" in explanation.lower()

    def test_explanation_for_empty_snapshot(self) -> None:
        """Explanation handles missing data gracefully."""
        empty = SignalSnapshot.empty()
        decision = evaluate_policy(empty, BALANCED)
        explanation = generate_explanation(decision)

        assert "SKIP" in explanation
        assert len(explanation) > 0


# --- Pipeline integration tests ---

class TestPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_with_provided_snapshot(self) -> None:
        """Pipeline produces a complete decision when given a snapshot."""
        snapshot = SignalSnapshot(
            price_usd=65000.0,
            price_7d_avg=65200.0,
            fee_rate_sat_vb=12.0,
            volatility_24h_pct=1.2,
        )
        decision = await run_pipeline(profile=BALANCED, snapshot=snapshot)

        assert decision.action in (Action.BUY, Action.SKIP, Action.WAIT)
        assert decision.explanation != ""
        assert decision.snapshot is not None
        assert len(decision.scores) == 3
        assert decision.reason != ""

    @pytest.mark.asyncio
    async def test_pipeline_invalid_profile_name(self) -> None:
        """Pipeline raises ValueError for unknown profile name."""
        snapshot = SignalSnapshot(price_usd=65000.0)
        with pytest.raises(ValueError, match="Unknown profile"):
            await run_pipeline(profile_name="nonexistent", snapshot=snapshot)

    @pytest.mark.asyncio
    async def test_pipeline_explanation_matches_action(self) -> None:
        """Pipeline explanation text matches the decision action."""
        snapshot = SignalSnapshot(
            price_usd=60000.0,
            price_7d_avg=63000.0,
            fee_rate_sat_vb=8.0,
            volatility_24h_pct=1.0,
        )
        decision = await run_pipeline(profile=BALANCED, snapshot=snapshot)

        assert decision.action.value.upper() in decision.explanation
