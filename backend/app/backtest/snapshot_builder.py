"""Convert historical WeeklyRow data into SignalSnapshots.

Each WeeklyRow becomes a SignalSnapshot that the existing policy engine
can evaluate — no changes needed to the scoring or evaluator code.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.backtest.data import WeeklyRow
from app.schemas import SignalSnapshot


def build_snapshot(row: WeeklyRow) -> SignalSnapshot:
    """Convert a single WeeklyRow into a SignalSnapshot.

    The snapshot uses the fee proxy (estimated sat/vB) as fee_rate_sat_vb,
    and mempool_size_bytes converted to MB for mempool_depth_mb. All other
    fields map directly.

    Staleness is set to 0 since historical data is "fresh" at its point in time.
    """
    return SignalSnapshot(
        timestamp=datetime.strptime(row.week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc),
        # Fee data
        fee_rate_sat_vb=row.fee_proxy_sat_vb,
        mempool_depth_mb=row.mempool_size_bytes / 1_000_000 if row.mempool_size_bytes is not None else None,
        # Price data
        price_usd=row.price_usd,
        price_7d_avg=row.price_7d_avg,
        price_30d_avg=row.price_30d_avg,
        # Volatility
        volatility_24h_pct=row.volatility_24h_pct,
        # No staleness — historical data is "fresh" at its time
        staleness_fees_s=0.0,
        staleness_price_s=0.0,
        staleness_onchain_s=0.0,
    )


def build_snapshots(rows: list[WeeklyRow]) -> list[SignalSnapshot]:
    """Convert a full series of WeeklyRows into SignalSnapshots."""
    return [build_snapshot(row) for row in rows]
