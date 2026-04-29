"""Historical data fetcher for backtesting.

Pulls weekly BTC price data from CoinGecko and mempool-proxy metrics from
Blockchain.com Charts. Results are cached as JSON files so that repeated
backtest runs don't hammer the APIs.

Data sources:
- CoinGecko: BTC/USD daily prices (free, 5+ years)
- Blockchain.com Charts: mempool size, tx count, avg confirmation time,
  total transaction fees. These are aggregated from their own Bitcoin nodes
  and serve as a useful historical proxy (not perfect ground truth).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

# Where cached data lives
CACHE_DIR = Path(__file__).resolve().parent / "cache"

# Blockchain.com chart names we care about
BLOCKCHAIN_CHARTS = {
    "price_usd": "market-price",
    "mempool_size_bytes": "mempool-size",
    "mempool_tx_count": "mempool-count",
    "avg_confirmation_minutes": "avg-confirmation-time",
    "total_fees_usd": "transaction-fees-usd",
    "daily_tx_count": "n-transactions",
}

BLOCKCHAIN_BASE = "https://api.blockchain.info/charts"


@dataclass
class DailyRow:
    """One day of historical data, aligned across all sources."""

    date: str  # ISO date YYYY-MM-DD
    price_usd: float | None = None
    mempool_size_bytes: float | None = None
    mempool_tx_count: float | None = None
    avg_confirmation_minutes: float | None = None
    total_fees_usd: float | None = None
    daily_tx_count: float | None = None  # confirmed txs per day (for fee proxy)


@dataclass
class WeeklyRow:
    """One week of aggregated data for the backtest."""

    week_start: str  # ISO date
    price_usd: float  # average price over the week
    price_7d_avg: float  # rolling 7-day average (same as price_usd for weekly)
    price_30d_avg: float  # rolling 30-day average
    volatility_24h_pct: float  # average daily |% change| during the week
    fee_proxy_sat_vb: float  # estimated fee rate derived from on-chain fee data
    mempool_size_bytes: float  # average mempool size during the week
    mempool_tx_count: float  # average mempool tx count during the week


def fetch_and_cache(
    start_date: date = date(2020, 1, 1),
    end_date: date | None = None,
    force_refresh: bool = False,
) -> list[WeeklyRow]:
    """Fetch historical data, cache it, and return weekly rows.

    Args:
        start_date: Start of the backtest window.
        end_date: End of the backtest window (defaults to today).
        force_refresh: If True, ignore cache and re-fetch.

    Returns:
        List of WeeklyRow, one per week, sorted chronologically.
    """
    if end_date is None:
        end_date = date.today()

    cache_file = CACHE_DIR / f"weekly_{start_date}_{end_date}.json"

    if cache_file.exists() and not force_refresh:
        with open(cache_file) as f:
            raw = json.load(f)
        return [WeeklyRow(**row) for row in raw]

    # Fetch daily data from all sources
    daily = _fetch_daily(start_date, end_date)

    # Aggregate to weekly
    weekly = _aggregate_weekly(daily)

    # Cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump([asdict(w) for w in weekly], f, indent=2)

    return weekly


def _fetch_daily(start_date: date, end_date: date) -> dict[str, DailyRow]:
    """Fetch daily data from Blockchain.com and merge by date."""
    daily: dict[str, DailyRow] = {}

    for field_name, chart_name in BLOCKCHAIN_CHARTS.items():
        print(f"  Fetching {chart_name}...")
        series = _fetch_blockchain_chart(chart_name, start_date, end_date)
        for iso_date, value in series.items():
            if iso_date not in daily:
                daily[iso_date] = DailyRow(date=iso_date)
            setattr(daily[iso_date], field_name, value)

    return daily


def _fetch_blockchain_chart(
    chart_name: str,
    start_date: date,
    end_date: date,
) -> dict[str, float]:
    """Fetch a single Blockchain.com chart series."""
    days = (end_date - start_date).days
    timespan = f"{days}days"
    # start parameter anchors the timespan to a specific date
    start_ts = int(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())

    url = f"{BLOCKCHAIN_BASE}/{chart_name}"
    params = {"timespan": timespan, "start": start_ts, "format": "json", "sampled": "false"}

    result: dict[str, float] = {}

    with httpx.Client(timeout=60.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    for point in data.get("values", []):
        ts = point["x"]
        val = point["y"]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        iso = dt.strftime("%Y-%m-%d")
        result[iso] = val

    # Be polite — small delay between API calls
    time.sleep(0.5)

    return result


def _aggregate_weekly(daily: dict[str, DailyRow]) -> list[WeeklyRow]:
    """Aggregate daily data into weekly rows.

    Weeks start on Monday. Each week computes:
    - Average price
    - 7-day and 30-day rolling average price
    - Average daily |% change| as volatility proxy
    - Estimated fee rate from on-chain fee data
    - Average mempool size and tx count
    """
    # Sort by date
    sorted_dates = sorted(daily.keys())
    if not sorted_dates:
        return []

    # Build ordered price list for rolling calculations
    all_prices: list[tuple[str, float]] = []
    for d in sorted_dates:
        row = daily[d]
        if row.price_usd is not None:
            all_prices.append((d, row.price_usd))

    # Group into ISO weeks
    weeks: dict[str, list[DailyRow]] = {}
    for d in sorted_dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        # ISO week start (Monday)
        week_start = dt - __import__("datetime").timedelta(days=dt.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(daily[d])

    # Build price lookup for rolling averages
    price_by_date: dict[str, float] = {d: p for d, p in all_prices}
    price_dates = [d for d, _ in all_prices]

    weekly_rows: list[WeeklyRow] = []
    sorted_weeks = sorted(weeks.keys())

    for week_key in sorted_weeks:
        days_in_week = weeks[week_key]

        # Average price this week
        week_prices = [r.price_usd for r in days_in_week if r.price_usd is not None]
        if not week_prices:
            continue
        avg_price = sum(week_prices) / len(week_prices)

        # 7-day rolling average (same as week avg for weekly data)
        price_7d = avg_price

        # 30-day rolling average
        week_end_dt = datetime.strptime(week_key, "%Y-%m-%d") + __import__("datetime").timedelta(days=6)
        thirty_days_ago = week_end_dt - __import__("datetime").timedelta(days=30)
        prices_30d = [
            price_by_date[d]
            for d in price_dates
            if thirty_days_ago.strftime("%Y-%m-%d") <= d <= week_end_dt.strftime("%Y-%m-%d")
        ]
        price_30d = sum(prices_30d) / len(prices_30d) if prices_30d else avg_price

        # Volatility: average |daily % change| during the week
        daily_changes: list[float] = []
        for i in range(1, len(week_prices)):
            if week_prices[i - 1] > 0:
                pct_change = abs((week_prices[i] - week_prices[i - 1]) / week_prices[i - 1]) * 100
                daily_changes.append(pct_change)
        volatility = sum(daily_changes) / len(daily_changes) if daily_changes else 0.0

        # Fee proxy: estimate sat/vB from total daily fees (USD) and daily confirmed tx count
        # Logic: total_fees_usd / daily_tx_count ≈ fee per tx in USD
        #        fee_per_tx_usd / price * 1e8 / assumed_tx_size ≈ sat/vB
        week_fees = [r.total_fees_usd for r in days_in_week if r.total_fees_usd is not None]
        week_daily_txcount = [r.daily_tx_count for r in days_in_week if r.daily_tx_count is not None]

        if week_fees and week_daily_txcount and avg_price > 0:
            avg_fee_usd = sum(week_fees) / len(week_fees)
            avg_daily_txs = sum(week_daily_txcount) / len(week_daily_txcount)
            if avg_daily_txs > 0:
                fee_per_tx_usd = avg_fee_usd / avg_daily_txs
                # Convert to sat/vB: (fee_usd / price_btc) * 1e8 / typical_tx_vbytes
                fee_per_tx_sats = (fee_per_tx_usd / avg_price) * 1e8
                fee_sat_vb = fee_per_tx_sats / 140.0  # typical P2WPKH tx size
            else:
                fee_sat_vb = 20.0  # fallback
        else:
            fee_sat_vb = 20.0  # fallback

        # Mempool metrics
        week_mempool_size = [r.mempool_size_bytes for r in days_in_week if r.mempool_size_bytes is not None]
        week_mempool_count = [r.mempool_tx_count for r in days_in_week if r.mempool_tx_count is not None]

        weekly_rows.append(WeeklyRow(
            week_start=week_key,
            price_usd=avg_price,
            price_7d_avg=price_7d,
            price_30d_avg=price_30d,
            volatility_24h_pct=volatility,
            fee_proxy_sat_vb=round(fee_sat_vb, 1),
            mempool_size_bytes=sum(week_mempool_size) / len(week_mempool_size) if week_mempool_size else 0.0,
            mempool_tx_count=sum(week_mempool_count) / len(week_mempool_count) if week_mempool_count else 0.0,
        ))

    return weekly_rows
