"""Pure scoring functions — one per signal category.

Each function takes a SignalSnapshot and a StrategyProfile and returns a
SignalScore with a normalised value (0.0 = strongly unfavourable, 1.0 = strongly
favourable) and a human-readable reason.

These functions have NO side effects, NO I/O, and NO dependencies on global state.
Given the same inputs, they always return the same output.
"""

from __future__ import annotations

from app.policy.profiles import StrategyProfile
from app.schemas import SignalScore, SignalSnapshot


def score_fees(snapshot: SignalSnapshot, profile: StrategyProfile) -> SignalScore:
    """Score the current fee environment.

    - Below low threshold → 1.0 (excellent — cheapest fees)
    - Between low and mid → 0.7 (good — reasonable fees)
    - Between mid and high → 0.35 (mediocre — fees are elevated)
    - Above high threshold → 0.0 (bad — fees are too expensive)
    - No data → 0.5 (neutral — can't assess)
    """
    fee = snapshot.fee_rate_sat_vb

    if fee is None:
        return SignalScore(
            name="fees",
            value=0.5,
            weight=profile.weight_fee,
            reason="No fee data available — scoring as neutral",
        )

    if fee <= profile.fee_threshold_low:
        value = 1.0
        reason = f"Fees very low ({fee:.0f} sat/vB ≤ {profile.fee_threshold_low:.0f} threshold)"
    elif fee <= profile.fee_threshold_mid:
        # Linear interpolation between low and mid
        t = (fee - profile.fee_threshold_low) / (
            profile.fee_threshold_mid - profile.fee_threshold_low
        )
        value = 1.0 - (t * 0.3)  # 1.0 down to 0.7
        reason = (
            f"Fees moderate ({fee:.0f} sat/vB, between "
            f"{profile.fee_threshold_low:.0f}–{profile.fee_threshold_mid:.0f})"
        )
    elif fee <= profile.fee_threshold_high:
        # Linear interpolation between mid and high
        t = (fee - profile.fee_threshold_mid) / (
            profile.fee_threshold_high - profile.fee_threshold_mid
        )
        value = 0.7 - (t * 0.35)  # 0.7 down to 0.35
        reason = (
            f"Fees elevated ({fee:.0f} sat/vB, between "
            f"{profile.fee_threshold_mid:.0f}–{profile.fee_threshold_high:.0f})"
        )
    else:
        value = 0.0
        reason = f"Fees too high ({fee:.0f} sat/vB > {profile.fee_threshold_high:.0f} threshold)"

    return SignalScore(name="fees", value=value, weight=profile.weight_fee, reason=reason)


def score_price(snapshot: SignalSnapshot, profile: StrategyProfile) -> SignalScore:
    """Score the current price relative to the 7-day moving average.

    - Below MA by more than dip_pct → 1.0 (strong dip — buy opportunity)
    - Near MA (within ±dip_pct and ±premium_pct) → 0.5 (neutral)
    - Above MA by more than premium_pct → 0.0 (overpriced — skip)
    - No data → 0.5 (neutral — can't assess)
    """
    price = snapshot.price_usd
    avg = snapshot.price_7d_avg

    if price is None or avg is None or avg == 0:
        return SignalScore(
            name="price",
            value=0.5,
            weight=profile.weight_price,
            reason="No price or moving average data — scoring as neutral",
        )

    pct_diff = ((price - avg) / avg) * 100  # negative = below average

    if pct_diff <= -profile.price_dip_pct:
        # Strong dip — scale from 0.75 to 1.0 based on how deep the dip is
        depth_beyond = abs(pct_diff) - profile.price_dip_pct
        value = min(1.0, 0.75 + (depth_beyond / 10.0))
        reason = (
            f"Price {abs(pct_diff):.1f}% below 7d avg "
            f"(${price:,.0f} vs ${avg:,.0f}) — buying the dip"
        )
    elif pct_diff >= profile.price_premium_pct:
        # Price premium — scale from 0.25 down to 0.0
        premium_beyond = pct_diff - profile.price_premium_pct
        value = max(0.0, 0.25 - (premium_beyond / 10.0))
        reason = (
            f"Price {pct_diff:.1f}% above 7d avg "
            f"(${price:,.0f} vs ${avg:,.0f}) — overpriced"
        )
    else:
        # Neutral zone — linear scale between dip and premium
        range_total = profile.price_dip_pct + profile.price_premium_pct
        if range_total > 0:
            # Map from -dip_pct..+premium_pct to 0.75..0.25
            t = (pct_diff + profile.price_dip_pct) / range_total
            value = 0.75 - (t * 0.5)  # 0.75 at dip edge, 0.25 at premium edge
        else:
            value = 0.5
        reason = (
            f"Price near 7d avg ({pct_diff:+.1f}%, "
            f"${price:,.0f} vs ${avg:,.0f})"
        )

    return SignalScore(name="price", value=value, weight=profile.weight_price, reason=reason)


def score_volatility(snapshot: SignalSnapshot, profile: StrategyProfile) -> SignalScore:
    """Score the current market volatility.

    - Below low threshold → 1.0 (calm market — safe to buy)
    - Between low and high → linear interpolation from 1.0 to 0.2
    - Above high threshold → 0.0 (turbulent — wait or skip)
    - No data → 0.5 (neutral — can't assess)
    """
    vol = snapshot.volatility_24h_pct

    if vol is None:
        return SignalScore(
            name="volatility",
            value=0.5,
            weight=profile.weight_volatility,
            reason="No volatility data — scoring as neutral",
        )

    if vol <= profile.volatility_low:
        value = 1.0
        reason = f"Low volatility ({vol:.1f}% ≤ {profile.volatility_low:.1f}%) — calm market"
    elif vol <= profile.volatility_high:
        # Linear interpolation
        t = (vol - profile.volatility_low) / (profile.volatility_high - profile.volatility_low)
        value = 1.0 - (t * 0.8)  # 1.0 down to 0.2
        reason = (
            f"Moderate volatility ({vol:.1f}%, between "
            f"{profile.volatility_low:.1f}%–{profile.volatility_high:.1f}%)"
        )
    else:
        value = 0.0
        reason = (
            f"High volatility ({vol:.1f}% > {profile.volatility_high:.1f}%) — "
            "market too turbulent"
        )

    return SignalScore(
        name="volatility", value=value, weight=profile.weight_volatility, reason=reason
    )
