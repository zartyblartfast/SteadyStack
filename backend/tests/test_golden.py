"""Golden scenario test runner.

Loads all YAML scenarios from tests/golden/ and verifies the policy engine
produces the expected action and confidence range for each one.

If a golden test fails, the DEFAULT ASSUMPTION is that the CODE is wrong,
not the scenario. See tests/golden/README.md for the rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.policy.evaluator import evaluate_policy
from app.policy.profiles import PRESETS
from app.schemas import Action, SignalSnapshot

GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_scenarios() -> list[tuple[str, dict[str, Any]]]:
    """Discover and load all YAML scenario files."""
    scenarios = []
    for yaml_file in sorted(GOLDEN_DIR.rglob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        label = f"{yaml_file.parent.name}/{yaml_file.stem}"
        scenarios.append((label, data))
    return scenarios


def _build_snapshot(signals: dict[str, Any]) -> SignalSnapshot:
    """Build a SignalSnapshot from a scenario's signals dict."""
    # Filter to only fields that SignalSnapshot accepts
    valid_fields = {f.name for f in SignalSnapshot.__dataclass_fields__.values()}
    filtered = {k: v for k, v in signals.items() if k in valid_fields}
    return SignalSnapshot(**filtered)


SCENARIOS = _load_scenarios()


@pytest.mark.parametrize(
    "label,scenario",
    SCENARIOS,
    ids=[s[0] for s in SCENARIOS],
)
def test_golden_scenario(label: str, scenario: dict[str, Any]) -> None:
    """Verify a golden scenario produces the expected decision."""
    snapshot = _build_snapshot(scenario["signals"])
    profile = PRESETS[scenario["profile"]]
    expected_action = Action(scenario["expected_action"])

    decision = evaluate_policy(snapshot, profile)

    # Assert action
    assert decision.action == expected_action, (
        f"[{label}] Expected {expected_action.value}, got {decision.action.value}. "
        f"Weighted reason: {decision.reason}"
    )

    # Assert confidence bounds if specified
    if "expected_min_confidence" in scenario:
        assert decision.confidence >= scenario["expected_min_confidence"], (
            f"[{label}] Confidence {decision.confidence:.3f} below minimum "
            f"{scenario['expected_min_confidence']}. Reason: {decision.reason}"
        )

    if "expected_max_confidence" in scenario:
        assert decision.confidence <= scenario["expected_max_confidence"], (
            f"[{label}] Confidence {decision.confidence:.3f} above maximum "
            f"{scenario['expected_max_confidence']}. Reason: {decision.reason}"
        )
