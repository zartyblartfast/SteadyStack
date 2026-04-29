# Testing Strategy

How SteadyStack tests are designed to verify **actual correctness**, not just confirm the code does what it currently does.

---

## The Problem

Most test suites are written by:
1. Writing the code.
2. Running it.
3. Asserting that the output matches whatever the code produced.

This creates tests that pass by definition. They detect regressions but never detect whether the logic was **correct in the first place**. For a financial decision engine, this is unacceptable.

## The Solution: Three Layers of Correctness

SteadyStack uses three independent layers, each catching a different class of error.

---

### Layer 1: Golden Scenarios (Specification-First)

A curated set of **hand-verified market scenarios** where the correct decision is determined **before any code is written**, based on domain knowledge and the documented policy rules.

**How it works:**

1. Select real historical market conditions from public data (mempool.space, CoinGecko archives).
2. For each scenario, a human determines the correct decision by reading the policy rules and applying them manually to the data. Document the reasoning.
3. Encode each scenario as a test case: `(SignalSnapshot, StrategyProfile) → expected Decision`.
4. The code must produce the documented decision. If it doesn't, the **code is wrong**, not the test.

**Example golden scenario:**

```yaml
scenario: "High fees, price near 7-day low"
date_sourced: 2025-01-15
source: mempool.space + CoinGecko historical
signals:
  fee_rate_sat_vb: 120
  price_usd: 42500
  price_7d_avg: 44200
  price_vs_7d_avg_pct: -3.84
  volatility_24h_pct: 1.2
  mempool_depth_mb: 85
profile: balanced
expected_action: SKIP
expected_reason: "Fees above high threshold (120 > 80 sat/vB) outweighs favourable price"
human_reasoning: >
  Price is 3.8% below the 7-day average, which would normally favour a buy.
  However, mempool fees are at 120 sat/vB — well above the balanced profile's
  high threshold of 80. The cost-saving from a better entry price would be
  wiped out by the high transaction fee. The correct action is SKIP and wait
  for fees to drop. This was verified by checking that fees dropped to 15 sat/vB
  within 48 hours on 2025-01-17.
```

**Key rules:**
- Golden scenarios are written **before** the implementation they test.
- The `human_reasoning` field is mandatory — it explains *why* this is the correct answer, not just *what* the answer is.
- Golden scenarios are reviewed by someone other than the person implementing the feature.
- The scenario dataset is version-controlled and grows over time.
- If a code change causes a golden test to fail, the default assumption is that the **code is wrong**. The golden scenario can only be changed with a documented justification.

---

### Layer 2: Invariant Tests (Property-Based)

Rules that must **always hold**, regardless of the specific input values. These catch errors that specific scenarios might miss.

**Examples of invariants:**

```python
# Confidence invariants
def test_confidence_never_exceeds_one(snapshot, profile):
    result = evaluate_policy(snapshot, profile)
    assert 0.0 <= result.confidence <= 1.0

def test_stale_data_reduces_confidence(snapshot, profile):
    fresh = evaluate_policy(snapshot, profile)
    stale_snapshot = snapshot.with_staleness(minutes=30)
    stale = evaluate_policy(stale_snapshot, profile)
    assert stale.confidence < fresh.confidence

# Safety invariants
def test_never_buy_with_zero_confidence(snapshot, profile):
    result = evaluate_policy(snapshot, profile)
    if result.confidence == 0.0:
        assert result.action != Action.BUY

def test_skip_when_all_data_missing(profile):
    empty = SignalSnapshot.empty()
    result = evaluate_policy(empty, profile)
    assert result.action == Action.SKIP

# Determinism invariant
def test_same_inputs_same_output(snapshot, profile):
    result_a = evaluate_policy(snapshot, profile)
    result_b = evaluate_policy(snapshot, profile)
    assert result_a == result_b

# Budget invariant
def test_recommended_amount_never_exceeds_remaining_budget(snapshot, profile, budget):
    result = evaluate_policy(snapshot, profile)
    if result.action == Action.BUY:
        assert result.amount <= budget.remaining
```

**How to generate inputs:**
- Use **property-based testing** (Hypothesis library) to generate random valid `SignalSnapshot` and `StrategyProfile` combinations.
- This tests thousands of input combinations, catching edge cases that hand-written scenarios miss.
- If Hypothesis finds a failing case, it minimises the input to the simplest reproduction — making debugging straightforward.

---

### Layer 3: Backtesting Against Historical Data

Run the engine against **months of real historical market data** and verify that it produces measurably better outcomes than naive weekly DCA.

**This is not a unit test — it is a system-level validation.**

**How it works:**

1. Collect historical data: hourly BTC prices, daily mempool fee averages, and on-chain metrics for a chosen period (e.g., 6-12 months).
2. Simulate the engine running on each buy window during that period.
3. Compare the simulated SteadyStack outcomes against a naive weekly DCA over the same period.
4. Verify that the success metrics hold:
   - Average acquisition cost at least 3-5% lower
   - Total fees paid measurably lower
   - >70% of skips were justified (price or fees improved within the wait window)

**Key rules:**
- Backtesting uses the **same policy code** as production. No separate backtesting logic.
- Historical data is stored as fixtures, not fetched live. Tests must be reproducible.
- Backtest results are recorded and tracked over time. If a code change degrades backtest performance, it requires justification before merging.
- Backtesting validates the **rules and thresholds**, not just the code. If the engine consistently underperforms naive DCA in backtests, the rules need to change — the code might be perfectly correct but the strategy is wrong.

---

## How the Three Layers Work Together

| Layer | What it catches | When it runs |
|---|---|---|
| **Golden scenarios** | Logic errors — code doesn't match the documented rules | Every commit (fast, unit tests) |
| **Invariants** | Edge cases, boundary errors, safety violations | Every commit (fast, property-based) |
| **Backtesting** | Strategy errors — rules are correct but produce bad outcomes | Before release, after rule changes |

A test suite that only has Layer 1 can have tests that are "correct" but based on wrong rules.  
A test suite that only has Layer 3 can pass overall but hide specific logic bugs.  
A test suite that only has Layer 2 proves safety but not correctness of specific decisions.  

**All three layers together** close the gap:
- Golden scenarios ensure individual decisions match human-verified expectations.
- Invariants ensure the engine is safe across all possible inputs.
- Backtesting ensures the strategy actually works in the real world.

---

## Practical Workflow

1. **Before implementing a policy rule**: write the golden scenario first. Document the expected decision and the human reasoning. Get it reviewed.
2. **While implementing**: add invariant tests for any property that should always hold.
3. **After implementing**: run the backtest suite and verify no degradation.
4. **When a bug is found**: add a golden scenario that reproduces it before fixing. The scenario stays in the suite forever.

---

## Golden Scenario Dataset

The golden scenarios will live in `backend/tests/golden/` as YAML files, grouped by the signal or rule they test:

```
backend/tests/golden/
├── fee_signals/          # Scenarios focused on fee-based decisions
├── price_signals/        # Scenarios focused on price-based decisions
├── volatility/           # Scenarios focused on volatility conditions
├── combined/             # Scenarios where multiple signals interact
├── edge_cases/           # Missing data, stale data, boundary values
└── README.md             # How to add and review golden scenarios
```

Each scenario file is a standalone YAML document with the structure shown above. A test runner loads all scenarios and asserts the engine produces the expected output for each one.
