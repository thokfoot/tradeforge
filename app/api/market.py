from __future__ import annotations

from datetime import date, timedelta
import random

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from app.api import deps

router = APIRouter(prefix="/api")


def default_range(interval: str) -> timedelta:
    if interval.endswith("m"):
        return timedelta(days=7)
    if interval.endswith("h"):
        return timedelta(days=60)
    return timedelta(days=730)


def bar_timestamp(ts, interval: str) -> str:
    if interval.endswith("m") or interval.endswith("h"):
        return ts.strftime("%Y-%m-%d %H:%M")
    return ts.strftime("%Y-%m-%d")


def generate_mock_bars(symbol: str, start: date, end: date, base_price: float = 2500.0) -> list[dict]:
    """Generate mock OHLCV bars for when live data is unavailable."""
    bars = []
    current = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    price = base_price
    while current <= end_ts:
        # Skip weekends
        if current.weekday() < 5:
            open_p = price * (1 + random.uniform(-0.02, 0.02))
            high = max(open_p, price) * (1 + random.uniform(0, 0.015))
            low = min(open_p, price) * (1 - random.uniform(0, 0.015))
            close = price * (1 + random.uniform(-0.015, 0.015))
            volume = random.uniform(1_000_000, 50_000_000)
            bars.append({
                "date": bar_timestamp(current, "1d"),
                "open": round(open_p, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": float(volume),
            })
            price = close
        current += timedelta(days=1)
    return bars


@router.get("/symbols")
def list_symbols(
    market: str = Query(..., description="IN | US | CRYPTO"),
) -> list[dict]:
    return [info.__dict__ for info in deps.provider_for(market).get_symbols()]


@router.get("/ohlcv/{symbol}")
def get_ohlcv(
    symbol: str,
    market: str = Query(...),
    interval: str = Query("1d"),
    start: date | None = Query(None),
    end: date | None = Query(None),
) -> dict:
    print(f"[market] Fetching candles for {symbol} market={market} interval={interval}")
    if start is None:
        start = date.today() - default_range(interval)
    if end is None:
        end = date.today()
    try:
        df = deps.provider_for(market).fetch_ohlcv(
            symbol, interval, pd.Timestamp(start), pd.Timestamp(end)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if df.empty:
        print(f"[market] No data for {symbol}, returning mock data")
        mock_bars = generate_mock_bars(symbol, start, end)
        return {
            "symbol": symbol,
            "market": market,
            "interval": interval,
            "bars": mock_bars,
        }
    bars = [
        {
            "date": bar_timestamp(ts, interval),
            "open": round(float(row["open"]), 4),
            "high": round(float(row["high"]), 4),
            "low": round(float(row["low"]), 4),
            "close": round(float(row["close"]), 4),
            "volume": float(row["volume"]),
        }
        for ts, row in df.iterrows()
    ]
    return {
        "symbol": symbol,
        "market": market,
        "interval": interval,
        "bars": bars,
    }
