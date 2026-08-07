from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path

ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        candidate = hash_password_with(password, salt, int(iterations))
        return candidate == stored
    except (ValueError, TypeError):
        return False


def hash_password_with(password: str, salt: str, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), iterations
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


class UserStore:
    def __init__(self, path: Path | None = None):
        self._dir = Path(path) if path else None
        self._users: dict[str, dict] = {}
        self._sessions: dict[str, dict] = {}
        if self._dir is not None:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        users_file = self._dir / "users.json"
        if users_file.exists():
            self._users = json.loads(users_file.read_text(encoding="utf-8"))
        sessions_file = self._dir / "sessions.json"
        if sessions_file.exists():
            self._sessions = json.loads(sessions_file.read_text(encoding="utf-8"))

    def _save(self) -> None:
        if self._dir is None:
            return
        (self._dir / "users.json").write_text(
            json.dumps(self._users, indent=2, default=str), encoding="utf-8"
        )
        (self._dir / "sessions.json").write_text(
            json.dumps(self._sessions, indent=2, default=str), encoding="utf-8"
        )

    def find_by_email(self, email: str) -> dict | None:
        lowered = email.strip().lower()
        for rec in self._users.values():
            if rec["email"] == lowered:
                return rec
        return None

    def get_user(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    def upsert_user(self, user_id: str, record: dict) -> None:
        self._users[user_id] = record
        self._save()

    def create_session(self, token: str, user_id: str, expires_at: datetime) -> None:
        self._sessions[token] = {
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
        }
        self._save()

    def get_session(self, token: str) -> dict | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        expires_at = datetime.fromisoformat(session["expires_at"])
        if expires_at < datetime.now():
            self._sessions.pop(token, None)
            self._save()
            return None
        return session
