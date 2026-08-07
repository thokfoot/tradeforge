from __future__ import annotations

from typing import Callable

import pandas as pd

from modules.shared.contracts import ScreenerRow

Loader = Callable[[str], pd.DataFrame]

NUMERIC_FILTERS = {
    "min_price": ("last_close", ">="),
    "max_price": ("last_close", "<="),
    "min_volume": ("avg_volume_20", ">="),
    "min_change_1d_pct": ("change_1d_pct", ">="),
    "min_change_5d_pct": ("change_5d_pct", ">="),
    "min_change_1m_pct": ("change_1m_pct", ">="),
    "min_change_3m_pct": ("change_3m_pct", ">="),
}
BOOL_FILTERS = {
    "above_sma_50": ("above_sma_50", True),
    "below_sma_50": ("above_sma_50", False),
    "above_sma_200": ("above_sma_200", True),
    "below_sma_200": ("above_sma_200", False),
}
SORTABLE = {
    "change_1d_pct",
    "change_5d_pct",
    "change_1m_pct",
    "change_3m_pct",
    "last_close",
    "avg_volume_20",
}


class ScreenerService:
    def __init__(self, loader: Loader):
        self._loader = loader

    def scan(
        self,
        symbols: list[str],
        filters: dict | None = None,
        limit: int = 50,
    ) -> list[ScreenerRow]:
        filters = filters or {}
        results: list[ScreenerRow] = []
        for symbol in symbols[:limit]:
            try:
                df = self._loader(symbol)
            except Exception:
                continue
            if df is None or df.empty or len(df) < 2:
                continue
            row = self._metrics(symbol, df)
            if self._matches(row, filters):
                results.append(row)
        sort_by = filters.get("sort_by", "change_1m_pct")
        if sort_by in SORTABLE:
            results.sort(key=lambda r: getattr(r, sort_by) if getattr(r, sort_by) is not None else -1e18, reverse=True)
        return results

    @staticmethod
    def _metrics(symbol: str, df: pd.DataFrame) -> ScreenerRow:
        close = df["close"]
        last = float(close.iloc[-1])
        return ScreenerRow(
            symbol=symbol,
            last_close=last,
            change_1d_pct=_pct_change(close, 1),
            change_5d_pct=_pct_change(close, 5),
            change_1m_pct=_pct_change(close, 21),
            change_3m_pct=_pct_change(close, 63),
            avg_volume_20=float(df["volume"].tail(20).mean()) if "volume" in df and len(df) >= 2 else None,
            above_sma_50=_above_sma(close, 50),
            above_sma_200=_above_sma(close, 200),
        )

    @staticmethod
    def _matches(row: ScreenerRow, filters: dict) -> bool:
        for key, (attr, op) in NUMERIC_FILTERS.items():
            value = filters.get(key)
            if value is None:
                continue
            current = getattr(row, attr)
            if current is None:
                return False
            if op == ">=" and not (current >= value):
                return False
            if op == "<=" and not (current <= value):
                return False
        for key, (attr, expected) in BOOL_FILTERS.items():
            if filters.get(key):
                if getattr(row, attr) is not expected:
                    return False
        return True


def _pct_change(close: pd.Series, window: int) -> float | None:
    if len(close) <= window:
        return None
    past = float(close.iloc[-(window + 1)])
    if past == 0:
        return None
    return (float(close.iloc[-1]) - past) / past * 100.0


def _above_sma(close: pd.Series, window: int) -> bool | None:
    if len(close) < window:
        return None
    sma = float(close.rolling(window).mean().iloc[-1])
    return float(close.iloc[-1]) > sma
