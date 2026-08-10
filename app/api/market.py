from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from app.api import deps

router = APIRouter(prefix="/api")

# Liquid NSE stocks prioritized at the top of the IN symbol list.
POPULAR_IN = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "KOTAKBANK",
]

_GSEC_RE = re.compile(r"^\d{2,4}GS\d{4}$")
_SGB_RE = re.compile(r"^SGB")


def is_gsec(symbol: str) -> bool:
    return bool(_GSEC_RE.match(symbol) or _SGB_RE.match(symbol))


def normalize_in_symbol(symbol: str) -> str:
    if symbol.endswith(".NS"):
        return symbol[:-3]
    return symbol


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


@router.get("/symbols")
def list_symbols(
    market: str = Query(..., description="IN | US | CRYPTO"),
) -> list[dict]:
    infos = deps.provider_for(market).get_symbols()
    if market.upper() != "IN":
        return [info.__dict__ for info in infos]

    gsecs: list[dict] = []
    stocks: list[dict] = []
    indices: list[dict] = []
    for info in infos:
        if is_gsec(info.symbol):
            gsecs.append(
                {
                    **info.__dict__,
                    "symbol": info.symbol,
                    "instrument_type": "GSEC",
                }
            )
        elif info.instrument_type == "index":
            indices.append(info.__dict__)
        else:
            stocks.append(
                {
                    **info.__dict__,
                    "symbol": f"{info.symbol}.NS",
                }
            )

    rank = {name: i for i, name in enumerate(POPULAR_IN)}
    stocks.sort(key=lambda s: (rank.get(normalize_in_symbol(s["symbol"]), 99), s["symbol"]))
    gsecs.sort(key=lambda s: s["symbol"])
    indices.sort(key=lambda s: s["symbol"])
    return stocks + indices + gsecs


@router.get("/ohlcv/{symbol}")
def get_ohlcv(
    symbol: str,
    market: str = Query(...),
    interval: str = Query("1d"),
    start: date | None = Query(None),
    end: date | None = Query(None),
) -> dict:
    # NSE stores symbols without the .NS suffix the UI appends
    if market.upper() == "IN":
        symbol = normalize_in_symbol(symbol)
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

    if df.empty and market.upper() == "IN":
        df = _yfinance_in_fallback(symbol, interval, start, end)

    if df.empty:
        print(f"[market] No data for {symbol}")
        return {
            "symbol": symbol,
            "market": market,
            "interval": interval,
            "bars": [],
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
    print(f"[market] Fetched {len(bars)} bars for {symbol}")
    return {
        "symbol": symbol,
        "market": market,
        "interval": interval,
        "bars": bars,
    }


def _yfinance_in_fallback(
    symbol: str, interval: str, start: date, end: date
) -> pd.DataFrame:
    """Try yfinance with .NS, then plain, then .BO for NSE symbols."""
    try:
        import yfinance as yf
    except ImportError:
        return pd.DataFrame()
    for candidate in (f"{symbol}.NS", symbol, f"{symbol}.BO"):
        try:
            df = yf.Ticker(candidate).history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                interval=interval,
                auto_adjust=True,
            )
        except Exception as exc:
            print(f"[market] yfinance {candidate} error: {exc}")
            continue
        if df is None or df.empty:
            print(f"[market] yfinance {candidate} empty")
            continue
        print(f"[market] yfinance {candidate} gave {len(df)} rows")
        out = pd.DataFrame(
            {
                "open": df["Open"],
                "high": df["High"],
                "low": df["Low"],
                "close": df["Close"],
                "volume": df["Volume"],
            }
        )
        out.index = pd.DatetimeIndex(pd.to_datetime(df.index)).tz_localize(None)
        out.index.name = "date"
        return out
    return pd.DataFrame()
