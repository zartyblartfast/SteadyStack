"""Strategy profiles — preset and custom configurations for the decision engine.

Each profile defines thresholds and weights that control how signals are
scored and combined. The same scoring functions are used regardless of
profile — only the parameters change.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyProfile:
    """Configuration for the decision engine's scoring and thresholds.

    All fee thresholds are in sat/vB. All price thresholds are percentages.
    Weights are relative — they are normalised to sum to 1.0 during evaluation.
    """

    name: str

    # --- Fee thresholds (sat/vB) ---
    fee_threshold_low: float   # Below this = strong buy signal
    fee_threshold_mid: float   # Below this = moderate buy signal
    fee_threshold_high: float  # Above this = skip signal (too expensive)

    # --- Price thresholds (% relative to moving average) ---
    price_dip_pct: float       # Below MA by this % = strong buy signal
    price_premium_pct: float   # Above MA by this % = skip signal (overpriced)

    # --- Volatility thresholds (%) ---
    volatility_low: float      # Below this = calm market, safe to buy
    volatility_high: float     # Above this = turbulent, consider waiting

    # --- Signal weights (relative, normalised during evaluation) ---
    weight_fee: float
    weight_price: float
    weight_volatility: float

    # --- Decision thresholds ---
    buy_score_threshold: float   # Weighted score must exceed this to BUY
    skip_score_threshold: float  # Weighted score below this = SKIP

    # --- Budget ---
    min_buy_usd: float = 10.0   # Minimum buy amount
    max_buy_usd: float = 500.0  # Maximum single buy amount


# --- Preset profiles ---

CONSERVATIVE = StrategyProfile(
    name="conservative",
    # Very sensitive to fees — only buys when fees are cheap
    fee_threshold_low=15.0,
    fee_threshold_mid=30.0,
    fee_threshold_high=50.0,
    # Requires a meaningful dip to trigger a buy
    price_dip_pct=3.0,
    price_premium_pct=2.0,
    # Low tolerance for volatility
    volatility_low=1.5,
    volatility_high=4.0,
    # Fee-dominant weighting
    weight_fee=0.5,
    weight_price=0.3,
    weight_volatility=0.2,
    # Higher bar to trigger a buy
    buy_score_threshold=0.65,
    skip_score_threshold=0.30,
)

BALANCED = StrategyProfile(
    name="balanced",
    # Moderate fee sensitivity
    fee_threshold_low=25.0,
    fee_threshold_mid=50.0,
    fee_threshold_high=80.0,
    # Moderate dip/premium thresholds
    price_dip_pct=2.0,
    price_premium_pct=3.0,
    # Moderate volatility tolerance
    volatility_low=2.0,
    volatility_high=5.0,
    # Even weighting
    weight_fee=0.4,
    weight_price=0.35,
    weight_volatility=0.25,
    # Moderate bar
    buy_score_threshold=0.55,
    skip_score_threshold=0.25,
)

AGGRESSIVE = StrategyProfile(
    name="aggressive",
    # High fee tolerance — willing to pay more
    fee_threshold_low=40.0,
    fee_threshold_mid=70.0,
    fee_threshold_high=120.0,
    # Buys on small dips, tolerates premiums
    price_dip_pct=1.0,
    price_premium_pct=5.0,
    # High volatility tolerance
    volatility_low=3.0,
    volatility_high=8.0,
    # Price-dominant weighting
    weight_fee=0.25,
    weight_price=0.45,
    weight_volatility=0.30,
    # Lower bar — buys more often
    buy_score_threshold=0.45,
    skip_score_threshold=0.20,
)

PRESETS: dict[str, StrategyProfile] = {
    "conservative": CONSERVATIVE,
    "balanced": BALANCED,
    "aggressive": AGGRESSIVE,
}
