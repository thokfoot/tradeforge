"""Postgres-backed store implementations matching JSON store interfaces."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from modules.shared.database import get_session
from modules.shared.models import (
    AlertNotification,
    AlertRule,
    EducationProgress,
    JournalEntry,
    PaperAccount,
    PaperOrder,
    PaperPosition,
    PaperTrade,
    SavedScan,
    Session as SessionModel,
    Strategy,
    User,
)


# ── Auth / User store ─────────────────────────────────────────────────

class PgUserStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def find_by_email(self, email: str) -> dict | None:
        user = self.db.query(User).filter(User.email == email.strip().lower()).first()
        return _user_to_dict(user) if user else None

    def get_user(self, user_id: str) -> dict | None:
        user = self.db.query(User).filter(User.id == user_id).first()
        return _user_to_dict(user) if user else None

    def upsert_user(self, user_id: str, record: dict) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.email = record.get("email", user.email)
            user.password_hash = record.get("password_hash", user.password_hash)
            user.plan = record.get("plan", user.plan)
        else:
            user = User(
                id=user_id,
                email=record["email"],
                password_hash=record["password_hash"],
                plan=record.get("plan", "free"),
            )
            self.db.add(user)
        self.db.commit()

    def create_session(self, token: str, user_id: str, expires_at: datetime) -> None:
        s = SessionModel(token=token, user_id=user_id, expires_at=expires_at)
        self.db.add(s)
        self.db.commit()

    def get_session(self, token: str) -> dict | None:
        s = self.db.query(SessionModel).filter(SessionModel.token == token).first()
        if s is None:
            return None
        if s.expires_at < datetime.utcnow():
            self.db.delete(s)
            self.db.commit()
            return None
        return {"user_id": s.user_id, "expires_at": s.expires_at.isoformat()}


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "plan": user.plan,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ── Journal store ─────────────────────────────────────────────────────

class PgJournalStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def load(self, user_id: str) -> list[dict]:
        rows = self.db.query(JournalEntry).filter(JournalEntry.user_id == user_id).order_by(JournalEntry.created_at).all()
        return [_entry_to_dict(r) for r in rows]

    def append(self, user_id: str, entry: dict) -> None:
        je = JournalEntry(
            entry_id=entry.get("entry_id", uuid.uuid4().hex[:12]),
            user_id=user_id,
            trade_id=entry.get("trade_id", ""),
            note=entry.get("note", ""),
            symbol=entry.get("symbol", ""),
            side=entry.get("side"),
            qty=entry.get("qty"),
            pnl=entry.get("pnl"),
            tags=entry.get("tags", []),
            rating=entry.get("rating"),
            lesson=entry.get("lesson", ""),
        )
        self.db.add(je)
        self.db.commit()

    def delete(self, user_id: str, entry_id: str) -> bool:
        je = self.db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id, JournalEntry.entry_id == entry_id
        ).first()
        if je is None:
            return False
        self.db.delete(je)
        self.db.commit()
        return True


def _entry_to_dict(je: JournalEntry) -> dict:
    return {
        "entry_id": je.entry_id,
        "user_id": je.user_id,
        "trade_id": je.trade_id,
        "note": je.note,
        "symbol": je.symbol,
        "side": je.side,
        "qty": je.qty,
        "pnl": je.pnl,
        "tags": je.tags or [],
        "rating": je.rating,
        "lesson": je.lesson,
        "created_at": je.created_at.isoformat() if je.created_at else None,
    }


# ── Alert store ───────────────────────────────────────────────────────

class PgAlertStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def load(self, user_id: str) -> dict:
        return {"rules": self.rules(user_id), "notifications": self.notifications(user_id)}

    def rules(self, user_id: str) -> list[dict]:
        rows = self.db.query(AlertRule).filter(
            AlertRule.user_id == user_id
        ).order_by(AlertRule.created_at).all()
        return [_rule_to_dict(r) for r in rows]

    def notifications(self, user_id: str) -> list[dict]:
        rows = self.db.query(AlertNotification).filter(
            AlertNotification.user_id == user_id
        ).order_by(AlertNotification.created_at.desc()).all()
        return [_notif_to_dict(r) for r in rows]

    def save_rules(self, user_id: str, rules: list[dict]) -> None:
        self.db.query(AlertRule).filter(AlertRule.user_id == user_id).delete()
        for r in rules:
            self.db.add(AlertRule(
                rule_id=r.get("rule_id", uuid.uuid4().hex[:12]),
                user_id=user_id,
                symbol=r["symbol"],
                market=r["market"],
                metric=r["metric"],
                condition=r["condition"],
                value=r["value"],
                active=r.get("active", True),
            ))
        self.db.commit()

    def add_notification(self, user_id: str, notification: dict) -> None:
        n = AlertNotification(
            id=notification.get("id", uuid.uuid4().hex[:12]),
            user_id=user_id,
            rule_id=notification.get("rule_id", ""),
            symbol=notification.get("symbol", ""),
            message=notification.get("message", ""),
        )
        self.db.add(n)
        self.db.commit()
        total = self.db.query(AlertNotification).filter(AlertNotification.user_id == user_id).count()
        if total > 200:
            oldest = self.db.query(AlertNotification).filter(
                AlertNotification.user_id == user_id
            ).order_by(AlertNotification.created_at.asc()).limit(total - 200).all()
            for o in oldest:
                self.db.delete(o)
            self.db.commit()

    def clear_notifications(self, user_id: str) -> int:
        count = self.db.query(AlertNotification).filter(AlertNotification.user_id == user_id).count()
        self.db.query(AlertNotification).filter(AlertNotification.user_id == user_id).delete()
        self.db.commit()
        return count

    def user_ids(self) -> list[str]:
        rows = self.db.query(AlertRule.user_id).distinct().all()
        return [r[0] for r in rows]


def _rule_to_dict(r: AlertRule) -> dict:
    return {
        "rule_id": r.rule_id,
        "user_id": r.user_id,
        "symbol": r.symbol,
        "market": r.market,
        "metric": r.metric,
        "condition": r.condition,
        "value": r.value,
        "active": r.active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _notif_to_dict(n: AlertNotification) -> dict:
    return {
        "id": n.id,
        "user_id": n.user_id,
        "rule_id": n.rule_id,
        "symbol": n.symbol,
        "message": n.message,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


# ── Scan store ────────────────────────────────────────────────────────

class PgScanStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def load(self, user_id: str) -> list[dict]:
        rows = self.db.query(SavedScan).filter(SavedScan.user_id == user_id).all()
        return [_scan_to_dict(r) for r in rows]

    def add(self, scan) -> None:
        s = SavedScan(
            id=scan.id,
            user_id=scan.user_id,
            name=scan.name,
            market=scan.market,
            filters=scan.filters,
            limit=scan.limit,
        )
        self.db.add(s)
        self.db.commit()

    def list(self, user_id: str) -> list:
        from modules.screener.scans import SavedScan as SS
        rows = self.db.query(SavedScan).filter(SavedScan.user_id == user_id).all()
        return [SS(id=r.id, user_id=r.user_id, name=r.name, market=r.market, filters=r.filters, limit=r.limit, created_at=r.created_at) for r in rows]

    def get(self, user_id: str, scan_id: str):
        from modules.screener.scans import SavedScan as SS
        r = self.db.query(SavedScan).filter(SavedScan.user_id == user_id, SavedScan.id == scan_id).first()
        if r is None:
            return None
        return SS(id=r.id, user_id=r.user_id, name=r.name, market=r.market, filters=r.filters, limit=r.limit, created_at=r.created_at)

    def delete(self, user_id: str, scan_id: str) -> bool:
        r = self.db.query(SavedScan).filter(SavedScan.user_id == user_id, SavedScan.id == scan_id).first()
        if r is None:
            return False
        self.db.delete(r)
        self.db.commit()
        return True


def _scan_to_dict(s: SavedScan) -> dict:
    return {
        "id": s.id, "user_id": s.user_id, "name": s.name,
        "market": s.market, "filters": s.filters, "limit": s.limit,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ── Education store ───────────────────────────────────────────────────

class PgEducationStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def completed(self, user_id: str) -> list[str]:
        rows = self.db.query(EducationProgress.lesson_id).filter(
            EducationProgress.user_id == user_id
        ).all()
        return [r[0] for r in rows]

    def mark(self, user_id: str, lesson_id: str) -> list[str]:
        existing = self.db.query(EducationProgress).filter(
            EducationProgress.user_id == user_id, EducationProgress.lesson_id == lesson_id
        ).first()
        if existing is None:
            self.db.add(EducationProgress(user_id=user_id, lesson_id=lesson_id))
            self.db.commit()
        return self.completed(user_id)


# ── Strategy store ────────────────────────────────────────────────────

class PgStrategyStore:
    def __init__(self, _path=None):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def load(self, strategy_id: str) -> list[dict]:
        rows = self.db.query(Strategy).filter(Strategy.strategy_id == strategy_id).order_by(Strategy.id).all()
        return [_strat_to_dict(r) for r in rows]

    def append(self, strategy_id: str, version: dict) -> None:
        s = Strategy(
            strategy_id=strategy_id,
            version=version.get("version", "v1"),
            code=version.get("code", ""),
            params=version.get("params"),
            author_user_id=version.get("author_user_id", ""),
        )
        self.db.add(s)
        self.db.commit()


def _strat_to_dict(s: Strategy) -> dict:
    return {
        "strategy_id": s.strategy_id, "version": s.version, "code": s.code,
        "params": s.params, "author_user_id": s.author_user_id,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ── Paper Trading store ───────────────────────────────────────────────

class PgAccountStore:
    def __init__(self, _path=None):
        self._db: Session | None = None
        self._ledgers: dict = {}

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = get_session()
        return self._db

    def get(self, user_id: str):
        from modules.paper_trading.store import Ledger
        from modules.shared.contracts.models import Position, Order, Trade

        if user_id in self._ledgers:
            return self._ledgers[user_id]

        acct = self.db.query(PaperAccount).filter(PaperAccount.user_id == user_id).first()
        if acct is None:
            acct = PaperAccount(user_id=user_id)
            self.db.add(acct)
            self.db.commit()

        positions = {}
        for p in self.db.query(PaperPosition).filter(PaperPosition.user_id == user_id).all():
            positions[p.symbol] = Position(symbol=p.symbol, qty=p.qty, avg_price=p.avg_price, ltp=p.ltp)

        orders = []
        for o in self.db.query(PaperOrder).filter(PaperOrder.user_id == user_id).all():
            orders.append(Order(
                id=o.id, user_id=o.user_id, symbol=o.symbol, side=o.side,
                order_type=o.order_type, qty=o.qty, price=o.price,
                sl=o.sl, tp=o.tp, status=o.status,
                filled_price=o.filled_price, filled_at=o.filled_at, created_at=o.created_at,
            ))

        trades = []
        for t in self.db.query(PaperTrade).filter(PaperTrade.user_id == user_id).all():
            trades.append(Trade(
                order_id=t.order_id, symbol=t.symbol, side=t.side,
                qty=t.qty, price=t.price, fees=t.fees, pnl=t.pnl,
                timestamp=t.timestamp, strategy_id=t.strategy_id,
            ))

        ledger = Ledger(user_id=user_id, balance=acct.balance)
        ledger.positions = positions
        ledger.orders = orders
        ledger.trades = trades
        self._ledgers[user_id] = ledger
        return ledger

    def save(self, user_id: str) -> None:
        if user_id not in self._ledgers:
            return
        ledger = self._ledgers[user_id]

        acct = self.db.query(PaperAccount).filter(PaperAccount.user_id == user_id).first()
        if acct is None:
            acct = PaperAccount(user_id=user_id)
            self.db.add(acct)
        acct.balance = ledger.balance

        self.db.query(PaperPosition).filter(PaperPosition.user_id == user_id).delete()
        for sym, pos in ledger.positions.items():
            self.db.add(PaperPosition(user_id=user_id, symbol=sym, qty=pos.qty, avg_price=pos.avg_price, ltp=pos.ltp))

        self.db.query(PaperOrder).filter(PaperOrder.user_id == user_id).delete()
        for o in ledger.orders:
            self.db.add(PaperOrder(
                id=o.id, user_id=o.user_id, symbol=o.symbol, side=o.side,
                order_type=o.order_type, qty=o.qty, price=o.price,
                sl=o.sl, tp=o.tp, status=o.status,
                filled_price=o.filled_price, filled_at=o.filled_at, created_at=o.created_at,
            ))

        self.db.query(PaperTrade).filter(PaperTrade.user_id == user_id).delete()
        for t in ledger.trades:
            self.db.add(PaperTrade(
                order_id=t.order_id, symbol=t.symbol, side=t.side,
                qty=t.qty, price=t.price, fees=t.fees, pnl=t.pnl,
                timestamp=t.timestamp, strategy_id=t.strategy_id,
            ))

        self.db.commit()
