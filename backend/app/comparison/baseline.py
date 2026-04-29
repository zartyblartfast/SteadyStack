"""Naive weekly DCA baseline calculator.

Simulates what a user would have achieved by buying a fixed amount of BTC
every week at market price with average mempool fees. This is the benchmark
against which SteadyStack performance is measured.

Pure functions — no I/O, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineBuy:
    """A single simulated baseline buy."""

    week_number: int
    price_usd: float
    fee_sat_vb: float
    amount_usd: float
    btc_acquired: float
    fee_cost_usd: float


@dataclass(frozen=True)
class BaselineResult:
    """Summary of a naive weekly DCA simulation."""

    total_invested_usd: float
    total_btc_acquired: float
    total_fees_usd: float
    average_cost_per_btc: float
    fee_pct_of_volume: float
    num_buys: int
    buys: tuple[BaselineBuy, ...]


def simulate_baseline(
    weekly_prices: list[float],
    weekly_fees: list[float],
    weekly_amount_usd: float,
    tx_size_vbytes: float = 140.0,
) -> BaselineResult:
    """Simulate naive weekly DCA over a series of weeks.

    Args:
        weekly_prices: BTC price at each weekly buy point (USD).
        weekly_fees: Average mempool fee at each weekly buy point (sat/vB).
        weekly_amount_usd: Fixed USD amount to buy each week.
        tx_size_vbytes: Assumed transaction size in virtual bytes (default 140 for
            a typical 1-in-2-out P2WPKH transaction).

    Returns:
        BaselineResult with total investment, BTC acquired, fees, and per-buy breakdown.
    """
    if len(weekly_prices) != len(weekly_fees):
        raise ValueError(
            f"weekly_prices ({len(weekly_prices)}) and weekly_fees ({len(weekly_fees)}) "
            "must have the same length"
        )

    buys: list[BaselineBuy] = []
    total_btc = 0.0
    total_fees_usd = 0.0
    total_invested = 0.0

    for i, (price, fee_rate) in enumerate(zip(weekly_prices, weekly_fees)):
        if price <= 0:
            continue

        # Fee cost in USD: (fee_rate sat/vB * tx_size vB) / 1e8 * price USD/BTC
        fee_cost_usd = (fee_rate * tx_size_vbytes / 1e8) * price

        # Net amount after fees
        net_amount = weekly_amount_usd - fee_cost_usd
        if net_amount <= 0:
            # Fee exceeds the buy amount — skip this week
            continue

        btc_acquired = net_amount / price

        buy = BaselineBuy(
            week_number=i + 1,
            price_usd=price,
            fee_sat_vb=fee_rate,
            amount_usd=weekly_amount_usd,
            btc_acquired=btc_acquired,
            fee_cost_usd=fee_cost_usd,
        )
        buys.append(buy)

        total_btc += btc_acquired
        total_fees_usd += fee_cost_usd
        total_invested += weekly_amount_usd

    avg_cost = total_invested / total_btc if total_btc > 0 else 0.0
    fee_pct = (total_fees_usd / total_invested * 100) if total_invested > 0 else 0.0

    return BaselineResult(
        total_invested_usd=total_invested,
        total_btc_acquired=total_btc,
        total_fees_usd=total_fees_usd,
        average_cost_per_btc=avg_cost,
        fee_pct_of_volume=fee_pct,
        num_buys=len(buys),
        buys=tuple(buys),
    )
