from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
from nsedata import nse

from modules.market_data.canonical import normalize_bhavcopy, normalize_indices
from modules.market_data.providers.base import ParquetBackedProvider
from modules.market_data.storage.parquet_store import ParquetStore
from modules.shared.contracts import Quote, SymbolInfo

log = logging.getLogger(__name__)


class NSEArchiveProvider(ParquetBackedProvider):
    market = "IN"
    currency = "INR"
    supported_intervals = {"1d"}

    def __init__(self, store: ParquetStore | None = None):
        super().__init__(store=store)
        self._bhav_cache: dict[date, pd.DataFrame] = {}
        self._index_cache: dict[date, pd.DataFrame] = {}
        self._index_slugs: set[str] | None = None

    def _fetch_bhavcopy(self, d: date) -> pd.DataFrame:
        if d not in self._bhav_cache:
            raw = nse.get(
                "capital_market", "equities_sme", "sec_bhavdata_full", d.isoformat()
            )
            self._bhav_cache[d] = normalize_bhavcopy(raw, d)
        return self._bhav_cache[d]

    def _fetch_indices(self, d: date) -> pd.DataFrame:
        if d not in self._index_cache:
            raw = nse.get("capital_market", "indices", "ind_close_all", d.isoformat())
            self._index_cache[d] = normalize_indices(raw, d)
            self._index_slugs = set(self._index_cache[d]["symbol"].unique())
        return self._index_cache[d]

    def _is_index(self, symbol: str) -> bool:
        if self._index_slugs is None:
            today = date.today()
            for attempt in range(5):
                try:
                    self._fetch_indices(today - timedelta(days=attempt))
                    break
                except Exception:
                    continue
        return symbol in (self._index_slugs or set())

    def _fetch_range(
        self, symbol: str, interval: str, start, end
    ) -> pd.DataFrame:
        parts = []
        for ts in pd.bdate_range(start.date(), end.date()):
            d = ts.date()
            try:
                day = (
                    self._fetch_indices(d)
                    if self._is_index(symbol)
                    else self._fetch_bhavcopy(d)
                )
            except Exception as exc:
                log.warning("no %s data on %s: %s", symbol, d, exc)
                continue
            row = day[day["symbol"] == symbol].drop(columns=["symbol"])
            if not row.empty:
                parts.append(row)
        return pd.concat(parts) if parts else self._empty()

    def fetch_quote(self, symbol: str) -> Quote:
        today = date.today()
        for attempt in range(5):
            d = today - timedelta(days=attempt)
            try:
                day = (
                    self._fetch_indices(d)
                    if self._is_index(symbol)
                    else self._fetch_bhavcopy(d)
                )
            except Exception:
                continue
            row = day[day["symbol"] == symbol]
            if row.empty:
                continue
            last = row.iloc[-1]
            volume = float(last["volume"]) if pd.notna(last["volume"]) else None
            return Quote(
                symbol=symbol,
                price=float(last["close"]),
                volume=volume,
                timestamp=d,
            )
        raise RuntimeError(f"No quote available for {symbol}")

    def get_symbols(self, as_of: date | None = None) -> list[SymbolInfo]:
        d = as_of or date.today()
        symbols: list[SymbolInfo] = []
        for attempt in range(5):
            day = d - timedelta(days=attempt)
            try:
                bhav = self._fetch_bhavcopy(day)
                break
            except Exception:
                continue
        else:
            bhav = None
        if bhav is not None:
            for sym in sorted(bhav["symbol"].unique()):
                symbols.append(
                    SymbolInfo(
                        symbol=sym,
                        market="IN",
                        exchange="NSE",
                        name=sym,
                        currency="INR",
                        instrument_type="stock",
                    )
                )
        for attempt in range(5):
            day = d - timedelta(days=attempt)
            try:
                idx = self._fetch_indices(day)
                break
            except Exception:
                continue
        else:
            idx = None
        if idx is not None:
            for sym, name in idx[["symbol", "name"]].drop_duplicates().itertuples(
                index=False
            ):
                symbols.append(
                    SymbolInfo(
                        symbol=sym,
                        market="IN",
                        exchange="NSE_INDEX",
                        name=name,
                        currency="INR",
                        instrument_type="index",
                    )
                )
        return symbols

    def backfill_indices(self, start: date, end: date) -> int:
        days = 0
        for ts in pd.bdate_range(start, end):
            d = ts.date()
            try:
                idx = self._fetch_indices(d)
            except Exception as exc:
                log.warning("indices %s failed: %s", d, exc)
                continue
            for symbol in idx["symbol"].unique():
                row = idx[idx["symbol"] == symbol].drop(columns=["symbol"])
                if self.store is not None:
                    self.store.write(self.market, "1d", symbol, row)
            days += 1
        return days
