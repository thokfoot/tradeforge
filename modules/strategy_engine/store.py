from __future__ import annotations

import json
from pathlib import Path

from modules.shared.safety import safe_id


class StrategyStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, strategy_id: str) -> Path:
        return self._path / f"{safe_id(strategy_id, 'strategy_id')}.json"

    def load(self, strategy_id: str) -> list[dict]:
        file = self._file(strategy_id)
        if not file.exists():
            return []
        return json.loads(file.read_text(encoding="utf-8"))

    def append(self, strategy_id: str, version: dict) -> None:
        versions = self.load(strategy_id)
        versions.append(version)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(strategy_id).write_text(
            json.dumps(versions, indent=2, default=str), encoding="utf-8"
        )
