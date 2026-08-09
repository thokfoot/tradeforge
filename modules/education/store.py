from __future__ import annotations

import json
from pathlib import Path

from modules.shared.safety import safe_id


class EducationStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def _file(self, user_id: str) -> Path:
        return self._path / f"{safe_id(user_id)}.json"

    def completed(self, user_id: str) -> list[str]:
        file = self._file(user_id)
        if not file.exists():
            return []
        return json.loads(file.read_text(encoding="utf-8"))

    def mark(self, user_id: str, lesson_id: str) -> list[str]:
        done = self.completed(user_id)
        if lesson_id not in done:
            done.append(lesson_id)
            self._path.mkdir(parents=True, exist_ok=True)
            self._file(user_id).write_text(
                json.dumps(done, indent=2), encoding="utf-8"
            )
        return done
