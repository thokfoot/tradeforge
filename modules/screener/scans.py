from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from modules.shared.safety import safe_id


@dataclass(frozen=True)
class SavedScan:
    id: str
    user_id: str
    name: str
    market: str
    filters: dict = field(default_factory=dict)
    limit: int = 50
    created_at: datetime | None = None


class ScanStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id)}.json"

    def load(self, user_id: str) -> list[dict]:
        file = self._file(user_id)
        if not file.exists():
            return []
        return json.loads(file.read_text(encoding="utf-8"))

    def _write(self, user_id: str, scans: list[dict]) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        self._file(user_id).write_text(
            json.dumps(scans, indent=2, default=str), encoding="utf-8"
        )

    def add(self, scan: SavedScan) -> SavedScan:
        scans = self.load(scan.user_id)
        scans.append(asdict(scan))
        self._write(scan.user_id, scans)
        return scan

    def list(self, user_id: str) -> list[SavedScan]:
        return [SavedScan(**s) for s in self.load(user_id)]

    def get(self, user_id: str, scan_id: str) -> SavedScan | None:
        for scan in self.list(user_id):
            if scan.id == scan_id:
                return scan
        return None

    def delete(self, user_id: str, scan_id: str) -> bool:
        remaining = [s for s in self.load(user_id) if s["id"] != scan_id]
        if len(remaining) == len(self.load(user_id)):
            return False
        self._write(user_id, remaining)
        return True


def new_saved_scan(user_id: str, name: str, market: str, filters: dict, limit: int) -> SavedScan:
    return SavedScan(
        id=uuid.uuid4().hex[:12],
        user_id=user_id,
        name=name,
        market=market,
        filters=filters,
        limit=limit,
        created_at=datetime.utcnow(),
    )
