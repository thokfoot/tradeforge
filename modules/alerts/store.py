from __future__ import annotations

import json
from pathlib import Path

from modules.shared.safety import safe_id


class AlertStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id)}.json"

    def load(self, user_id: str) -> dict:
        file = self._file(user_id)
        if not file.exists():
            return {"rules": [], "notifications": []}
        return json.loads(file.read_text(encoding="utf-8"))

    def _write(self, user_id: str, data: dict) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def rules(self, user_id: str) -> list[dict]:
        return self.load(user_id)["rules"]

    def notifications(self, user_id: str) -> list[dict]:
        return self.load(user_id)["notifications"]

    def save_rules(self, user_id: str, rules: list[dict]) -> None:
        data = self.load(user_id)
        data["rules"] = rules
        self._write(user_id, data)

    def add_notification(self, user_id: str, notification: dict) -> None:
        data = self.load(user_id)
        data["notifications"].insert(0, notification)
        data["notifications"] = data["notifications"][:200]
        self._write(user_id, data)

    def clear_notifications(self, user_id: str) -> int:
        data = self.load(user_id)
        count = len(data["notifications"])
        data["notifications"] = []
        self._write(user_id, data)
        return count

    def user_ids(self) -> list[str]:
        if not self._path.exists():
            return []
        return [f.stem for f in self._path.glob("*.json")]
