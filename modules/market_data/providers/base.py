from __future__ import annotations

import logging
from datetime import timedelta

import pandas as pd

log = logging.getLogger(__name__)

CANONICAL_COLUMNS = ["open", "high", "low", "close", "volume"]


class ParquetBackedProvider:
    market = "UNKNOWN"
    currency = ""
    supported_intervals: set[str] = {"1d"}
    allow_remote_gap_fill = True

    def __init__(self, store=None):
        self.store = store

    def _fetch_range(self, symbol: str, interval: str, start, end) -> pd.DataFrame:
        raise NotImplementedError

    def _empty(self) -> pd.DataFrame:
        return pd.DataFrame(columns=CANONICAL_COLUMNS).set_index(
            pd.DatetimeIndex([], name="date")
        )

    def _read_local(self, symbol: str, interval: str, start_d, end_d) -> list[pd.DataFrame]:
        if self.store is None:
            return []
        local = self.store.read(self.market, interval, symbol)
        if local is None or local.empty:
            return []
        window = local[(local.index.date >= start_d) & (local.index.date <= end_d)]
        return [window] if not window.empty else []

    @staticmethod
    def _uncovered_ranges(start_d, end_d, covered):
        covered = sorted(c for c in covered if start_d <= c <= end_d)
        ranges = []
        cursor = start_d
        for c in covered:
            if c > cursor:
                ranges.append((cursor, c - timedelta(days=1)))
            cursor = c + timedelta(days=1)
        if cursor <= end_d:
            ranges.append((cursor, end_d))
        return ranges

    def fetch_ohlcv(
        self, symbol: str, interval: str, start, end
    ) -> pd.DataFrame:
        if interval not in self.supported_intervals:
            raise ValueError(
                f"{type(self).__name__} supports intervals "
                f"{sorted(self.supported_intervals)}, got {interval!r}"
            )
        start_d = pd.Timestamp(start).date()
        end_d = pd.Timestamp(end).date()
        parts = self._read_local(symbol, interval, start_d, end_d)
        if parts and not self.allow_remote_gap_fill:
            result = pd.concat(parts)
            return result[~result.index.duplicated(keep="last")].sort_index()
        covered = {ts.date() for df in parts for ts in df.index}
        for gap_start, gap_end in self._uncovered_ranges(start_d, end_d, covered):
            business_days = pd.bdate_range(gap_start, gap_end)
            if business_days.empty:
                continue
            gap_start = business_days[0].date()
            gap_end = business_days[-1].date()
            try:
                df = self._fetch_range(
                    symbol, interval, pd.Timestamp(gap_start), pd.Timestamp(gap_end)
                )
            except Exception as exc:
                log.warning(
                    "fetch %s %s %s..%s failed: %s",
                    symbol, interval, gap_start, gap_end, exc,
                )
                continue
            if df is None or df.empty:
                continue
            parts.append(df)
            if self.store is not None:
                self.store.write(self.market, interval, symbol, df)
        if not parts:
            return self._empty()
        result = pd.concat(parts)
        result = result[~result.index.duplicated(keep="last")].sort_index()
        return result

    def backfill(
        self, symbols: list[str], interval: str = "1d", start=None, end=None
    ) -> dict[str, int]:
        if start is None:
            raise ValueError("backfill requires start")
        if end is None:
            raise ValueError("backfill requires end")
        return {symbol: len(self.fetch_ohlcv(symbol, interval, start, end)) for symbol in symbols}
