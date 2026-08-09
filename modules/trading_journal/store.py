from __future__ import annotations

import json
from pathlib import Path

from modules.shared.safety import safe_id


class JournalStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id)}.json"

    def load(self, user_id: str) -> list[dict]:
        file = self._file(user_id)
        if not file.exists():
            return []
        return json.loads(file.read_text(encoding="utf-8"))

    def append(self, user_id: str, entry: dict) -> None:
        entries = self.load(user_id)
        entries.append(entry)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(entries, indent=2, default=str), encoding="utf-8"
        )

    def delete(self, user_id: str, entry_id: str) -> bool:
        entries = self.load(user_id)
        remaining = [e for e in entries if e["entry_id"] != entry_id]
        if len(remaining) == len(entries):
            return False
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(remaining, indent=2, default=str), encoding="utf-8"
        )
        return True
