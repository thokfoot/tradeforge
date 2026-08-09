from __future__ import annotations

import logging
import os
from datetime import timedelta

import pandas as pd
import yfinance as yf

from modules.market_data.providers.base import ParquetBackedProvider
from modules.market_data.storage.parquet_store import ParquetStore
from modules.shared.contracts import Quote, SymbolInfo

log = logging.getLogger(__name__)

POPULAR_US = [
    ("AAPL", "stock"), ("MSFT", "stock"), ("NVDA", "stock"), ("GOOGL", "stock"),
    ("AMZN", "stock"), ("META", "stock"), ("TSLA", "stock"), ("AMD", "stock"),
    ("NFLX", "stock"), ("PLTR", "stock"), ("JPM", "stock"), ("BAC", "stock"),
    ("V", "stock"), ("KO", "stock"), ("PEP", "stock"), ("WMT", "stock"),
    ("JNJ", "stock"), ("PG", "stock"), ("XOM", "stock"), ("DIS", "stock"),
    ("BA", "stock"), ("MCD", "stock"), ("INTC", "stock"), ("IBM", "stock"),
    ("ORCL", "stock"), ("CRM", "stock"), ("ADBE", "stock"), ("CSCO", "stock"),
    ("QCOM", "stock"), ("AVGO", "stock"), ("UBER", "stock"), ("ABNB", "stock"),
    ("SHOP", "stock"), ("SNOW", "stock"), ("COIN", "stock"), ("TSM", "stock"),
    ("BABA", "stock"), ("SPY", "etf"), ("QQQ", "etf"), ("DIA", "etf"),
    ("IWM", "etf"), ("GLD", "etf"), ("SLV", "etf"), ("USO", "etf"), ("TLT", "etf"),
]

US_INDICES = [
    ("^GSPC", "S&P 500"),
    ("^DJI", "Dow Jones Industrial Average"),
    ("^IXIC", "Nasdaq Composite"),
    ("^NDX", "Nasdaq 100"),
    ("^RUT", "Russell 2000"),
    ("^VIX", "CBOE Volatility Index"),
    ("^NYA", "NYSE Composite"),
    ("^OEX", "S&P 100"),
    ("^MID", "S&P MidCap 400"),
    ("^SML", "S&P SmallCap 600"),
    ("^W5000", "Wilshire 5000"),
    ("^SOX", "PHLX Semiconductor"),
]


def to_canonical(yf_df: pd.DataFrame) -> pd.DataFrame:
    if yf_df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]).set_index(
            pd.DatetimeIndex([], name="date")
        )
    out = pd.DataFrame(
        {
            "open": yf_df["Open"],
            "high": yf_df["High"],
            "low": yf_df["Low"],
            "close": yf_df["Close"],
            "volume": yf_df["Volume"],
        }
    )
    out.index = pd.DatetimeIndex(pd.to_datetime(yf_df.index).tz_convert("UTC")).tz_localize(None)
    out.index.name = "date"
    return out


class YFinanceProvider(ParquetBackedProvider):
    market = "US"
    currency = "USD"
    supported_intervals = {"1d", "1h", "1m"}
    allow_remote_gap_fill = os.getenv("ENVIRONMENT", "development").lower() == "production"

    def __init__(self, store: ParquetStore | None = None):
        super().__init__(store=store)

    def _fetch_range(
        self, symbol: str, interval: str, start, end
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(
            start=start.date(),
            end=end.date() + timedelta(days=1),
            interval=interval,
            auto_adjust=False,
        )
        return to_canonical(hist)

    def fetch_quote(self, symbol: str) -> Quote:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist.empty:
            raise RuntimeError(f"No quote available for {symbol}")
        last = hist.iloc[-1]
        return Quote(
            symbol=symbol,
            price=float(last["Close"]),
            volume=float(last["Volume"]) if pd.notna(last["Volume"]) else None,
            timestamp=pd.Timestamp(hist.index[-1]).tz_localize(None),
        )

    def get_symbols(self) -> list[SymbolInfo]:
        stocks = [
            SymbolInfo(
                symbol=symbol,
                market="US",
                exchange="US",
                name=symbol,
                currency="USD",
                instrument_type=kind,
            )
            for symbol, kind in POPULAR_US
        ]
        indices = [
            SymbolInfo(
                symbol=symbol,
                market="US",
                exchange="INDEX",
                name=name,
                currency="USD",
                instrument_type="index",
            )
            for symbol, name in US_INDICES
        ]
        return indices + stocks
