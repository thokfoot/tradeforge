from __future__ import annotations

import logging
import os
from datetime import date, timedelta

import pandas as pd
from nsedata import nse

from modules.market_data.canonical import normalize_bhavcopy, normalize_indices
from modules.market_data.providers.base import ParquetBackedProvider
from modules.market_data.storage.parquet_store import ParquetStore
from modules.shared.contracts import Quote, SymbolInfo

log = logging.getLogger(__name__)

INDEX_DISPLAY_NAMES = {
    "NIFTY50": "NIFTY 50",
    "NIFTYBANK": "NIFTY Bank / Bank Nifty",
    "NIFTYTOTALMARKET": "NIFTY Total Market",
    "NIFTY100": "NIFTY 100",
    "NIFTY200": "NIFTY 200",
    "NIFTY500": "NIFTY 500",
    "NIFTYNEXT50": "NIFTY Next 50",
    "NIFTYMIDCAP50": "NIFTY Midcap 50",
    "NIFTYSMALLCAP50": "NIFTY Smallcap 50",
    "NIFTYFINANCIALSERVICES": "NIFTY Financial Services",
    "NIFTYPRIVATEBANK": "NIFTY Private Bank",
    "NIFTYPSUBANK": "NIFTY PSU Bank",
    "NIFTYIT": "NIFTY IT",
    "NIFTYFMCG": "NIFTY FMCG",
    "NIFTYPHARMA": "NIFTY Pharma",
    "NIFTYAUTO": "NIFTY Auto",
    "NIFTYMETAL": "NIFTY Metal",
    "NIFTYREALTY": "NIFTY Realty",
    "NIFTYENERGY": "NIFTY Energy",
    "NIFTYINFRASTRUCTURE": "NIFTY Infrastructure",
    "NIFTYHEALTHCAREINDEX": "NIFTY Healthcare",
}


class _MissingTradingDay(Exception):
    pass


def _is_not_found(exc: Exception) -> bool:
    return "404" in str(exc)


class NSEArchiveProvider(ParquetBackedProvider):
    market = "IN"
    currency = "INR"
    supported_intervals = {"1d"}
    allow_remote_gap_fill = os.getenv("ENVIRONMENT", "development").lower() == "production"

    def __init__(self, store: ParquetStore | None = None):
        super().__init__(store=store)
        self._bhav_cache: dict[date, pd.DataFrame] = {}
        self._index_cache: dict[date, pd.DataFrame] = {}
        self._missing_bhav_days: set[date] = set()
        self._missing_index_days: set[date] = set()
        self._index_slugs: set[str] | None = None

    def _fetch_bhavcopy(self, d: date) -> pd.DataFrame:
        if d in self._missing_bhav_days:
            raise _MissingTradingDay(d)
        if d not in self._bhav_cache:
            try:
                raw = nse.get(
                    "capital_market", "equities_sme", "sec_bhavdata_full", d.isoformat()
                )
            except Exception as exc:
                if _is_not_found(exc):
                    self._missing_bhav_days.add(d)
                    raise _MissingTradingDay(d) from exc
                raise
            self._bhav_cache[d] = normalize_bhavcopy(raw, d)
        return self._bhav_cache[d]

    def _fetch_indices(self, d: date) -> pd.DataFrame:
        if d in self._missing_index_days:
            raise _MissingTradingDay(d)
        if d not in self._index_cache:
            try:
                raw = nse.get("capital_market", "indices", "ind_close_all", d.isoformat())
            except Exception as exc:
                if _is_not_found(exc):
                    self._missing_index_days.add(d)
                    raise _MissingTradingDay(d) from exc
                raise
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
            except _MissingTradingDay:
                continue
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
            except _MissingTradingDay:
                continue
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
        local_dir = self.store.root / self.market / "1d" if self.store is not None else None
        local_paths = sorted(local_dir.glob("*.parquet")) if local_dir is not None and local_dir.exists() else []
        if local_paths:
            return [
                SymbolInfo(
                    symbol=path.stem,
                    market="IN",
                    exchange="NSE",
                    name=INDEX_DISPLAY_NAMES.get(path.stem, path.stem),
                    currency="INR",
                    instrument_type="index" if path.stem.startswith("NIFTY") else "stock",
                )
                for path in local_paths
            ]
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
            except _MissingTradingDay:
                continue
            except Exception as exc:
                log.warning("indices %s failed: %s", d, exc)
                continue
            for symbol in idx["symbol"].unique():
                row = idx[idx["symbol"] == symbol].drop(columns=["symbol"])
                if self.store is not None:
                    self.store.write(self.market, "1d", symbol, row)
            days += 1
        return days

    def backfill(
        self, symbols: list[str], interval: str = "1d", start=None, end=None
    ) -> dict[str, int]:
        if interval != "1d":
            raise ValueError("India backfill supports only '1d'")
        if start is None or end is None:
            raise ValueError("backfill requires start and end")
        symbols = list(dict.fromkeys(symbols))
        counts = {symbol: 0 for symbol in symbols}
        pending: dict[str, list[pd.DataFrame]] = {symbol: [] for symbol in symbols}

        def flush() -> None:
            for symbol, frames in pending.items():
                if not frames:
                    continue
                df = pd.concat(frames)
                if self.store is not None:
                    self.store.write(self.market, interval, symbol, df)
                counts[symbol] += len(df)
                pending[symbol] = []

        trading_days = 0
        for ts in pd.bdate_range(start, end):
            try:
                day = self._fetch_bhavcopy(ts.date())
            except _MissingTradingDay:
                continue
            trading_days += 1
            for symbol in symbols:
                row = day[day["symbol"] == symbol].drop(columns=["symbol"])
                if not row.empty:
                    pending[symbol].append(row)
            if trading_days % 10 == 0:
                flush()
        flush()
        return counts
