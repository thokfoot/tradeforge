from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta

from modules.auth_billing.store import UserStore, hash_password, verify_password
from modules.shared.contracts import Session, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_PLANS = ("free", "pro")


class AuthService:
    def __init__(self, store: UserStore, token_ttl_days: int = 30):
        self._store = store
        self._ttl = timedelta(days=token_ttl_days)

    def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        if not EMAIL_RE.fullmatch(email):
            raise ValueError("invalid email address")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        if self._store.find_by_email(email) is not None:
            raise ValueError("email already registered")
        user_id = secrets.token_hex(6)
        self._store.upsert_user(
            user_id,
            {
                "id": user_id,
                "email": email,
                "password_hash": hash_password(password),
                "plan": "free",
                "created_at": datetime.now().isoformat(),
            },
        )
        return User(id=user_id, email=email, plan="free")

    def login(self, email: str, password: str) -> Session:
        record = self._store.find_by_email(email)
        if record is None or not verify_password(password, record["password_hash"]):
            raise ValueError("invalid email or password")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + self._ttl
        self._store.create_session(token, record["id"], expires_at)
        return Session(user_id=record["id"], token=token, expires_at=expires_at)

    def create_subscription(self, user_id: str, plan: str) -> User:
        if plan not in VALID_PLANS:
            raise ValueError("invalid plan")
        record = self._store.get_user(user_id)
        if record is None:
            raise KeyError("user not found")
        record["plan"] = plan
        self._store.upsert_user(user_id, record)
        return User(id=user_id, email=record["email"], plan=plan)

    def get_user(self, user_id: str) -> User | None:
        record = self._store.get_user(user_id)
        if record is None:
            return None
        return User(id=record["id"], email=record["email"], plan=record["plan"])

    def user_for_token(self, token: str) -> User | None:
        session = self._store.get_session(token)
        if session is None:
            return None
        return self.get_user(session["user_id"])
