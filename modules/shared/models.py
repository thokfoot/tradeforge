"""SQLAlchemy ORM models for Postgres-backed stores."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _uid() -> str:
    return uuid4().hex[:12]


# ── Auth ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)


# ── Strategies ────────────────────────────────────────────────────────

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    params = Column(JSONB, nullable=True)
    author_user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Journal ───────────────────────────────────────────────────────────

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    entry_id = Column(String, primary_key=True, default=_uid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    trade_id = Column(String, nullable=False)
    note = Column(Text, nullable=False, default="")
    symbol = Column(String, nullable=False, default="")
    side = Column(String, nullable=True)
    qty = Column(Integer, nullable=True)
    pnl = Column(Float, nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    rating = Column(Integer, nullable=True)
    lesson = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Alerts ────────────────────────────────────────────────────────────

class AlertRule(Base):
    __tablename__ = "alert_rules"

    rule_id = Column(String, primary_key=True, default=_uid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    market = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertNotification(Base):
    __tablename__ = "alert_notifications"

    id = Column(String, primary_key=True, default=_uid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    rule_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Screener ──────────────────────────────────────────────────────────

class SavedScan(Base):
    __tablename__ = "saved_scans"

    id = Column(String, primary_key=True, default=_uid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    market = Column(String, nullable=False)
    filters = Column(JSONB, nullable=False, default=dict)
    limit = Column(Integer, nullable=False, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Education ─────────────────────────────────────────────────────────

class EducationProgress(Base):
    __tablename__ = "education_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False, primary_key=True)
    lesson_id = Column(String, nullable=False, primary_key=True)
    completed_at = Column(DateTime, default=datetime.utcnow)


# ── Paper Trading ─────────────────────────────────────────────────────

class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    balance = Column(Float, nullable=False, default=100000.0)
    initial_capital = Column(Float, nullable=False, default=100000.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaperPosition(Base):
    __tablename__ = "paper_positions"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_paper_position"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("paper_accounts.user_id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    ltp = Column(Float, nullable=False, default=0.0)


class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id = Column(String, primary_key=True, default=_uid)
    user_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="OPEN")
    filled_price = Column(Float, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    order_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    strategy_id = Column(String, nullable=True)
