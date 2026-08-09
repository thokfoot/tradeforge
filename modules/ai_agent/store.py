from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from modules.shared.safety import safe_id


class AgentBacktestStore:
    """Per-user JSON persistence of agent-run backtests (with authz + safe_id)."""

    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id, 'user_id')}.json"

    def _load(self, user_id: str) -> dict:
        file = self._file(user_id)
        if not file.exists():
            return {}
        return json.loads(file.read_text(encoding="utf-8"))

    def _write(self, user_id: str, data: dict) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def save(
        self, user_id: str, *, dsl: dict, plan_text: str, metrics: dict, summary: str
    ) -> dict:
        record_id = uuid.uuid4().hex[:12]
        safe_id(record_id, "id")
        record = {
            "id": record_id,
            "user_id": user_id,
            "dsl": dsl,
            "plan_text": plan_text,
            "metrics": metrics,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat(),
        }
        data = self._load(user_id)
        data[record_id] = record
        self._write(user_id, data)
        return record

    def get(self, user_id: str, record_id: str) -> dict | None:
        safe_id(record_id, "id")
        record = self._load(user_id).get(record_id)
        if record is None:
            return None
        if record.get("user_id") != user_id:
            return None
        return record

    def list(self, user_id: str) -> list[dict]:
        data = self._load(user_id)
        return [
            data[rid]
            for rid in sorted(data, key=lambda r: data[r].get("created_at", ""), reverse=True)
        ]
