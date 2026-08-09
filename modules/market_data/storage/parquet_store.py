from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.shared.safety import safe_id


class ParquetStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, market: str, interval: str, symbol: str) -> Path:
        return (
            self.root
            / safe_id(market, "market")
            / safe_id(interval, "interval")
            / f"{safe_id(symbol, 'symbol')}.parquet"
        )

    def write(self, market: str, interval: str, symbol: str, df: pd.DataFrame) -> None:
        if df.empty:
            return
        path = self._path(market, interval, symbol)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.read(market, interval, symbol)
        if existing is not None and not existing.empty:
            df = pd.concat([existing, df])
            df = df[~df.index.duplicated(keep="last")].sort_index()
        df.to_parquet(path)

    def read(self, market: str, interval: str, symbol: str) -> pd.DataFrame | None:
        path = self._path(market, interval, symbol)
        if not path.exists():
            return None
        df = pd.read_parquet(path)
        if "date" in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index("date")
        df.index = pd.DatetimeIndex(df.index)
        df.index.name = "date"
        return df

    def has(self, market: str, interval: str, symbol: str) -> bool:
        return self._path(market, interval, symbol).exists()
