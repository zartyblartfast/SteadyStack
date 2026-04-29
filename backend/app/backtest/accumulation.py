"""Accumulation-focused DCA engine for backtesting.

Core philosophy: ALWAYS BUY. Never skip a week. Maximize BTC accumulation by:
1. Buying MORE during dips (price below moving average)
2. Buying LESS during premiums (but still buying — never zero)
3. Saving on fees where it makes sense (fee-weighted adjustment)

The user has a fixed monthly budget. The engine distributes capital across
weeks, front-loading into dip opportunities and pulling back during premiums.
Unspent budget rolls forward and must be fully deployed by month end.

Three profiles control how aggressively the engine responds to dips:
- Conservative (Steady Stacker): narrow range, consistent accumulation
- Balanced (Dip Buyer): moderate range, meaningful dip response
- Aggressive (Deep Dip Hunter): wide range, buys hard into crashes
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log


@dataclass(frozen=True)
class AccumulationProfile:
    """Configuration for the accumulation engine."""

    name: str

    # Multiplier range: how much to scale the base amount
    min_multiplier: float  # floor (premium conditions)
    max_multiplier: float  # ceiling (deep dip conditions)

    # Price reference: use 30d MA as anchor
    # These define the % below/above 30d MA that maps to the multiplier range
    dip_full_pct: float     # at this % below 30d MA, use max_multiplier
    premium_full_pct: float  # at this % above 30d MA, use min_multiplier

    # Fee adjustment: slight reduction when fees are very high
    fee_high_threshold: float   # sat/vB above which to reduce slightly
    fee_penalty_factor: float   # multiply amount by this when fees are extreme (e.g., 0.9)

    # Monthly budget enforcement: force-deploy remaining budget
    force_deploy_week: int  # week of month to force-deploy remaining budget (4 = last week)


# --- Preset profiles ---

CONSERVATIVE_ACC = AccumulationProfile(
    name="conservative",
    min_multiplier=0.8,
    max_multiplier=1.3,
    dip_full_pct=15.0,
    premium_full_pct=15.0,
    fee_high_threshold=60.0,
    fee_penalty_factor=0.95,
    force_deploy_week=4,
)

BALANCED_ACC = AccumulationProfile(
    name="balanced",
    min_multiplier=0.6,
    max_multiplier=1.6,
    dip_full_pct=15.0,
    premium_full_pct=15.0,
    fee_high_threshold=70.0,
    fee_penalty_factor=0.92,
    force_deploy_week=4,
)

AGGRESSIVE_ACC = AccumulationProfile(
    name="aggressive",
    min_multiplier=0.5,
    max_multiplier=2.0,
    dip_full_pct=15.0,
    premium_full_pct=15.0,
    fee_high_threshold=80.0,
    fee_penalty_factor=0.90,
    force_deploy_week=4,
)

ACC_PRESETS: dict[str, AccumulationProfile] = {
    "conservative": CONSERVATIVE_ACC,
    "balanced": BALANCED_ACC,
    "aggressive": AGGRESSIVE_ACC,
}


@dataclass
class AccumulationDecision:
    """Output of the accumulation engine for a single week."""

    buy_amount_usd: float   # how much to buy this week
    multiplier: float       # the computed multiplier (for reporting)
    price_position_pct: float  # % above/below 30d MA
    fee_adjusted: bool      # whether fee penalty was applied
    reason: str


def compute_buy_amount(
    base_amount: float,
    price_usd: float,
    price_30d_avg: float,
    fee_sat_vb: float,
    profile: AccumulationProfile,
    reserve_usd: float = 0.0,
    is_month_end: bool = False,
) -> AccumulationDecision:
    """Compute how much to buy this week.

    Args:
        base_amount: The user's standard weekly DCA amount.
        price_usd: Current BTC price.
        price_30d_avg: 30-day moving average price.
        fee_sat_vb: Current estimated fee rate.
        profile: Accumulation profile.
        reserve_usd: Unspent budget carried forward from previous weeks.
        is_month_end: If True, force-deploy all remaining reserve.

    Returns:
        AccumulationDecision with the recommended buy amount.
    """
    # Price position relative to 30d MA
    if price_30d_avg > 0:
        price_pct = ((price_usd - price_30d_avg) / price_30d_avg) * 100
    else:
        price_pct = 0.0

    # Map price position to multiplier using smooth linear interpolation
    # Below MA (negative pct_diff) → higher multiplier (buy more)
    # Above MA (positive pct_diff) → lower multiplier (buy less)
    if price_pct <= -profile.dip_full_pct:
        # Deep dip: max multiplier
        multiplier = profile.max_multiplier
    elif price_pct >= profile.premium_full_pct:
        # Strong premium: min multiplier
        multiplier = profile.min_multiplier
    else:
        # Linear interpolation between max and min
        # At -dip_full_pct → max_multiplier
        # At +premium_full_pct → min_multiplier
        total_range = profile.dip_full_pct + profile.premium_full_pct
        if total_range > 0:
            # Normalise: 0 = deep dip edge, 1 = premium edge
            t = (price_pct + profile.dip_full_pct) / total_range
            multiplier = profile.max_multiplier - t * (profile.max_multiplier - profile.min_multiplier)
        else:
            multiplier = 1.0

    # Fee adjustment: slight reduction when fees are extreme
    fee_adjusted = False
    if fee_sat_vb > profile.fee_high_threshold:
        multiplier *= profile.fee_penalty_factor
        fee_adjusted = True

    # Compute amount
    buy_amount = base_amount * multiplier

    # Add reserve if this is month-end (force deploy)
    if is_month_end and reserve_usd > 0:
        buy_amount += reserve_usd

    # Build reason
    if price_pct < -5:
        tone = "buying the dip"
    elif price_pct < -1:
        tone = "slight discount"
    elif price_pct > 5:
        tone = "premium price, reducing"
    elif price_pct > 1:
        tone = "slight premium"
    else:
        tone = "near average"

    reason = (
        f"BUY ${buy_amount:.0f} — price {price_pct:+.1f}% vs 30d avg "
        f"({tone}, {multiplier:.2f}x)"
    )
    if fee_adjusted:
        reason += f" [fee penalty: {fee_sat_vb:.0f} sat/vB > {profile.fee_high_threshold:.0f}]"
    if is_month_end and reserve_usd > 0:
        reason += f" [+${reserve_usd:.0f} month-end reserve]"

    return AccumulationDecision(
        buy_amount_usd=buy_amount,
        multiplier=multiplier,
        price_position_pct=price_pct,
        fee_adjusted=fee_adjusted,
        reason=reason,
    )
