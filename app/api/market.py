from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from app.api import deps

router = APIRouter(prefix="/api")


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
    if start is None:
        start = date.today() - timedelta(days=730)
    if end is None:
        end = date.today()
    try:
        df = deps.provider_for(market).fetch_ohlcv(
            symbol, interval, pd.Timestamp(start), pd.Timestamp(end)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if df.empty:
        raise HTTPException(status_code=404, detail=f"no data for {symbol}")
    bars = [
        {
            "date": ts.strftime("%Y-%m-%d"),
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
