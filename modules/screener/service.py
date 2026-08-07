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
    "min_rsi": ("rsi_14", ">="),
    "max_rsi": ("rsi_14", "<="),
    "min_bb_position": ("bb_position", ">="),
    "max_bb_position": ("bb_position", "<="),
    "min_vol_ratio": ("vol_ratio_20", ">="),
}
BOOL_FILTERS = {
    "above_sma_20": ("above_sma_20", True),
    "below_sma_20": ("above_sma_20", False),
    "above_sma_50": ("above_sma_50", True),
    "below_sma_50": ("above_sma_50", False),
    "above_sma_200": ("above_sma_200", True),
    "below_sma_200": ("above_sma_200", False),
    "macd_above_signal": ("macd_above_signal", True),
    "macd_below_signal": ("macd_above_signal", False),
}
SORTABLE = {
    "change_1d_pct",
    "change_5d_pct",
    "change_1m_pct",
    "change_3m_pct",
    "last_close",
    "avg_volume_20",
    "rsi_14",
    "bb_position",
    "vol_ratio_20",
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
            avg_volume_20=_avg_volume(df),
            above_sma_50=_above_sma(close, 50),
            above_sma_200=_above_sma(close, 200),
            rsi_14=_rsi(close, 14),
            bb_position=_bb_position(close, 20),
            vol_ratio_20=_vol_ratio(df, 20),
            above_sma_20=_above_sma(close, 20),
            macd_above_signal=_macd_above_signal(close),
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


def _rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) <= period:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return float(100.0 - 100.0 / (1.0 + rs))


def _bb_position(close: pd.Series, period: int = 20) -> float | None:
    if len(close) < period:
        return None
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = mid + 2 * std
    lower = mid - 2 * std
    band = float(upper.iloc[-1] - lower.iloc[-1])
    if band == 0:
        return None
    return float((close.iloc[-1] - lower.iloc[-1]) / band)


def _vol_ratio(df: pd.DataFrame, window: int = 20) -> float | None:
    if "volume" not in df or len(df) < window + 1:
        return None
    avg = float(df["volume"].iloc[-window - 1:-1].mean())
    if avg == 0:
        return None
    return float(df["volume"].iloc[-1]) / avg


def _avg_volume(df: pd.DataFrame) -> float | None:
    if "volume" not in df or len(df) < 2:
        return None
    return float(df["volume"].tail(20).mean())


def _macd_above_signal(close: pd.Series) -> bool | None:
    if len(close) < 35:
        return None
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return bool(float(macd.iloc[-1]) > float(signal.iloc[-1]))
