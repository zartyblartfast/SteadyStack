"""Property-based invariant tests for the policy engine.

These test properties that must ALWAYS hold, regardless of input values.
Uses Hypothesis to generate thousands of random valid inputs.
"""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given, settings

from app.policy.evaluator import evaluate_policy
from app.policy.profiles import BALANCED, CONSERVATIVE, AGGRESSIVE, StrategyProfile
from app.schemas import Action, SignalSnapshot

# --- Strategies for generating random valid inputs ---

signal_snapshots = st.builds(
    SignalSnapshot,
    fee_rate_sat_vb=st.one_of(st.none(), st.floats(min_value=1, max_value=500)),
    mempool_depth_mb=st.one_of(st.none(), st.floats(min_value=0, max_value=300)),
    fastest_fee=st.one_of(st.none(), st.floats(min_value=1, max_value=500)),
    half_hour_fee=st.one_of(st.none(), st.floats(min_value=1, max_value=500)),
    hour_fee=st.one_of(st.none(), st.floats(min_value=1, max_value=500)),
    economy_fee=st.one_of(st.none(), st.floats(min_value=1, max_value=500)),
    price_usd=st.one_of(st.none(), st.floats(min_value=1000, max_value=500000)),
    price_1h_change_pct=st.one_of(st.none(), st.floats(min_value=-50, max_value=50)),
    price_24h_change_pct=st.one_of(st.none(), st.floats(min_value=-50, max_value=50)),
    price_7d_change_pct=st.one_of(st.none(), st.floats(min_value=-50, max_value=50)),
    price_7d_avg=st.one_of(st.none(), st.floats(min_value=1000, max_value=500000)),
    price_30d_avg=st.one_of(st.none(), st.floats(min_value=1000, max_value=500000)),
    volatility_24h_pct=st.one_of(st.none(), st.floats(min_value=0, max_value=50)),
    volatility_7d_pct=st.one_of(st.none(), st.floats(min_value=0, max_value=50)),
    staleness_fees_s=st.floats(min_value=0, max_value=3600),
    staleness_price_s=st.floats(min_value=0, max_value=3600),
    staleness_onchain_s=st.floats(min_value=0, max_value=3600),
)

profiles = st.sampled_from([CONSERVATIVE, BALANCED, AGGRESSIVE])


class TestConfidenceInvariants:
    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=500)
    def test_confidence_between_zero_and_one(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """Confidence must always be in [0.0, 1.0]."""
        decision = evaluate_policy(snapshot, profile)
        assert 0.0 <= decision.confidence <= 1.0

    @given(profile=profiles)
    def test_all_data_missing_gives_zero_confidence(
        self, profile: StrategyProfile
    ) -> None:
        """When all data is missing, confidence must be 0."""
        empty = SignalSnapshot.empty()
        decision = evaluate_policy(empty, profile)
        assert decision.confidence == 0.0


class TestSafetyInvariants:
    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=500)
    def test_never_buy_with_zero_confidence(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """The engine must never recommend BUY when confidence is zero."""
        decision = evaluate_policy(snapshot, profile)
        if decision.confidence == 0.0:
            assert decision.action != Action.BUY

    @given(profile=profiles)
    def test_empty_snapshot_is_skip(self, profile: StrategyProfile) -> None:
        """An empty snapshot (total API failure) must always SKIP."""
        empty = SignalSnapshot.empty()
        decision = evaluate_policy(empty, profile)
        assert decision.action == Action.SKIP


class TestDeterminismInvariant:
    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=200)
    def test_same_inputs_same_output(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """Given identical inputs, the engine must always produce the same output."""
        result_a = evaluate_policy(snapshot, profile)
        result_b = evaluate_policy(snapshot, profile)
        assert result_a.action == result_b.action
        assert result_a.confidence == result_b.confidence
        assert result_a.reason == result_b.reason


class TestActionInvariants:
    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=500)
    def test_action_is_valid_enum(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """Action must always be one of BUY, SKIP, WAIT."""
        decision = evaluate_policy(snapshot, profile)
        assert decision.action in (Action.BUY, Action.SKIP, Action.WAIT)

    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=500)
    def test_reason_is_not_empty(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """Every decision must have a non-empty reason."""
        decision = evaluate_policy(snapshot, profile)
        assert len(decision.reason) > 0

    @given(snapshot=signal_snapshots, profile=profiles)
    @settings(max_examples=500)
    def test_scores_are_present(
        self, snapshot: SignalSnapshot, profile: StrategyProfile
    ) -> None:
        """Every decision must include exactly 3 signal scores."""
        decision = evaluate_policy(snapshot, profile)
        assert len(decision.scores) == 3
        names = {s.name for s in decision.scores}
        assert names == {"fees", "price", "volatility"}
