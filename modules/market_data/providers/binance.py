from __future__ import annotations

import logging

import httpx
import pandas as pd

from modules.market_data.providers.base import ParquetBackedProvider
from modules.market_data.storage.parquet_store import ParquetStore
from modules.shared.contracts import Quote, SymbolInfo

log = logging.getLogger(__name__)

BASE_URL = "https://api.binance.com/api/v3"
KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades", "taker_buy_base",
    "taker_buy_quote", "ignore",
]


def klines_to_df(rows: list[list]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]).set_index(
            pd.DatetimeIndex([], name="date")
        )
    idx = pd.to_datetime([r[0] for r in rows], unit="ms", utc=True).tz_localize(None)
    df = pd.DataFrame(
        {
            "open": [float(r[1]) for r in rows],
            "high": [float(r[2]) for r in rows],
            "low": [float(r[3]) for r in rows],
            "close": [float(r[4]) for r in rows],
            "volume": [float(r[5]) for r in rows],
        },
        index=pd.DatetimeIndex(idx, name="date"),
    )
    return df


class BinanceProvider(ParquetBackedProvider):
    market = "CRYPTO"
    currency = "USDT"
    supported_intervals = {"1d", "1h", "1m"}

    def __init__(self, store: ParquetStore | None = None, client: httpx.Client | None = None):
        super().__init__(store=store)
        self._client = client or httpx.Client(timeout=30.0)

    def _fetch_range(
        self, symbol: str, interval: str, start, end
    ) -> pd.DataFrame:
        start_ms = int(pd.Timestamp(start).timestamp() * 1000)
        end_ms = int(pd.Timestamp(end).timestamp() * 1000) + 86_400_000
        all_rows: list[list] = []
        cursor = start_ms
        while cursor <= end_ms:
            resp = self._client.get(
                f"{BASE_URL}/klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": cursor,
                    "limit": 1000,
                },
            )
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                break
            all_rows.extend(rows)
            cursor = int(rows[-1][0]) + 1
        return klines_to_df(all_rows)

    def fetch_quote(self, symbol: str) -> Quote:
        resp = self._client.get(
            f"{BASE_URL}/klines",
            params={"symbol": symbol, "interval": "1d", "limit": 1},
        )
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            raise RuntimeError(f"No quote available for {symbol}")
        last = rows[-1]
        return Quote(
            symbol=symbol,
            price=float(last[4]),
            volume=float(last[5]),
            timestamp=pd.to_datetime(last[0], unit="ms"),
        )

    def get_symbols(self) -> list[SymbolInfo]:
        resp = self._client.get(f"{BASE_URL}/exchangeInfo")
        resp.raise_for_status()
        data = resp.json()
        out: list[SymbolInfo] = []
        for s in data.get("symbols", []):
            if s.get("status") != "TRADING":
                continue
            if s.get("quoteAsset") != "USDT":
                continue
            out.append(
                SymbolInfo(
                    symbol=s["symbol"],
                    market="CRYPTO",
                    exchange="BINANCE",
                    name=s["baseAsset"],
                    currency="USDT",
                    instrument_type="crypto",
                )
            )
        return out
