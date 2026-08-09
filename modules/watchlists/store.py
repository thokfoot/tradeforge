from __future__ import annotations

import json
from pathlib import Path

from modules.shared.safety import safe_id


class WatchlistStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id)}.json"

    def load(self, user_id: str) -> dict:
        file = self._file(user_id)
        if not file.exists():
            return {}
        return json.loads(file.read_text(encoding="utf-8"))

    def _write(self, user_id: str, data: dict) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def list(self, user_id: str) -> dict[str, list[str]]:
        return self.load(user_id)

    def add(self, user_id: str, market: str, symbol: str) -> dict[str, list[str]]:
        data = self.load(user_id)
        data.setdefault(market, [])
        if symbol not in data[market]:
            data[market].append(symbol)
        self._write(user_id, data)
        return data

    def remove(self, user_id: str, market: str, symbol: str) -> dict[str, list[str]]:
        data = self.load(user_id)
        if market in data and symbol in data[market]:
            data[market] = [s for s in data[market] if s != symbol]
        self._write(user_id, data)
        return data
