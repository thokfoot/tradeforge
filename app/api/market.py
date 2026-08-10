from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from app.api import deps

IST = timezone(timedelta(hours=5, minutes=30))
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


def ist_now() -> datetime:
    return datetime.now(IST)


def _is_market_open(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    return time(9, 15) <= now.time() <= time(15, 30)

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
    now = ist_now()
    print(f"[market] Fetching candles for {symbol} market={market} interval={interval} as_of={now.isoformat()}")

    if market.upper() == "IN":
        df, meta, source = _yahoo_live(symbol, interval, start, end)
        if df is not None and not df.empty:
            print(f"[market] LIVE {source}: {len(df)} bars, last={df.index[-1]} ({now})")
            return _ohlcv_response(symbol, market, interval, df, now, source=source)
        print(f"[market] live fetch empty, falling back to NSE archive for {symbol}")

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
            "as_of_ist": now.isoformat(),
            "market_open": _is_market_open(now),
            "bars": [],
        }
    return _ohlcv_response(symbol, market, interval, df, now)


def _ohlcv_response(
    symbol: str,
    market: str,
    interval: str,
    df: pd.DataFrame,
    now: datetime,
    source: str = "archive",
) -> dict:
    bars = []
    live_time_str = df.attrs.get("live_time_str") if hasattr(df, "attrs") else None
    for i, (ts, row) in enumerate(df.iterrows()):
        if interval == "1d":
            d = ts.date() if isinstance(ts, pd.Timestamp) else pd.Timestamp(ts).date()
            close_ist = datetime.combine(d, time(15, 30), tzinfo=IST)
            time_unix = int(close_ist.timestamp())
            time_str = live_time_str if (i == len(df) - 1 and live_time_str) else close_ist.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_ist = pd.Timestamp(ts)
            ts_ist = ts_ist.tz_localize(IST) if ts_ist.tzinfo is None else ts_ist.tz_convert(IST)
            time_unix = int(ts_ist.timestamp())
            time_str = ts_ist.strftime("%Y-%m-%d %H:%M:%S")
        bars.append(
            {
                "date": bar_timestamp(ts, interval),
                "time": time_unix,
                "time_str": time_str,
                "open": round(float(row["open"]), 4),
                "high": round(float(row["high"]), 4),
                "low": round(float(row["low"]), 4),
                "close": round(float(row["close"]), 4),
                "volume": float(row["volume"]),
            }
        )
    if interval == "1d" and bars:
        print(f"1D last candle: {bars[-1]['time_str']}")
    print(f"[market] Fetched {len(bars)} bars for {symbol} source={source}")
    return {
        "symbol": symbol,
        "market": market,
        "interval": interval,
        "as_of_ist": now.isoformat(),
        "market_open": _is_market_open(now),
        "source": source,
        "bars": bars,
    }


def _yahoo_live(
    symbol: str, interval: str, start: date | None, end: date | None
) -> tuple[pd.DataFrame | None, dict, str]:
    """Live NSE candles straight from Yahoo's chart API (bypasses broken yfinance lib).

    Tries .NS, plain, then .BO. For 1m/5m/1h it uses the intraday endpoint; for
    1d it merges the current live session into the archived daily series.
    """
    if interval not in ("1m", "5m", "15m", "30m", "1h", "1d"):
        return None, {}, ""
    base = symbol[:-3] if symbol.endswith(".NS") else symbol
    for candidate in (f"{base}.NS", base, f"{base}.BO"):
        df, meta = _yahoo_chart(candidate, interval)
        if df is None or df.empty:
            continue
        if interval == "1d":
            live, live_meta = _yahoo_chart(candidate, "1m")
            if live is not None and not live.empty:
                _merge_today_live(df, live)
        return df, meta, f"yahoo:{candidate}"
    return None, {}, ""


def _merge_today_live(daily: pd.DataFrame, live: pd.DataFrame) -> None:
    """Replace today's daily bar with OHLCV aggregated from live 1m bars and
    record the last live time so the API can return it instead of midnight."""
    today = ist_now().date()
    live_today = live[live.index.date == today]
    if live_today.empty:
        return
    last_live_ts = live_today.index[-1]
    agg = pd.DataFrame(
        {
            "open": [live_today["open"].dropna().iloc[0]],
            "high": [live_today["high"].max()],
            "low": [live_today["low"].min()],
            "close": [live_today["close"].dropna().iloc[-1]],
            "volume": [live_today["volume"].sum()],
        },
        index=[pd.Timestamp(today)],
    )
    daily.loc[pd.Timestamp(today)] = agg.iloc[0]
    daily.sort_index(inplace=True)
    daily.attrs["live_time_str"] = last_live_ts.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[market] merged live {today}: close={agg.iloc[0]['close']} last_live={daily.attrs['live_time_str']}")


def _yahoo_chart(symbol: str, interval: str) -> tuple[pd.DataFrame | None, dict]:
    if interval == "1d":
        range_ = "6mo"
    elif interval == "1m":
        range_ = "5d"
    else:
        range_ = "1mo"
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.request.quote(symbol)}?interval={interval}&range={range_}"
    )
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[market] yahoo {symbol} error: {exc}")
        return None, {}
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return None, {}
    res = result[0]
    meta = res.get("meta") or {}
    ts = res.get("timestamp") or []
    quote = ((res.get("indicators") or {}).get("quote") or [{}])[0]
    if not ts:
        return pd.DataFrame(), meta
    idx = pd.DatetimeIndex([datetime.fromtimestamp(t, IST) for t in ts], name="date")
    out = pd.DataFrame(
        {
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "volume": quote.get("volume"),
        },
        index=idx,
    )
    out = out.dropna(subset=["close"]).drop_duplicates()
    if interval == "1d":
        out.index = pd.DatetimeIndex([ts.date() for ts in out.index], name="date")
    else:
        out.index = pd.DatetimeIndex([ts.replace(second=0, microsecond=0) for ts in out.index], name="date")
    return out, meta


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
