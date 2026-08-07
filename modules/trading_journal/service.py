from __future__ import annotations

import secrets
from dataclasses import asdict
from datetime import datetime

import pandas as pd

from modules.shared.contracts import JournalEntry, Trade
from modules.trading_journal.store import JournalStore


class JournalService:
    def __init__(self, store: JournalStore):
        self._store = store

    def add_entry(
        self,
        user_id: str,
        trade_id: str,
        note: str,
        symbol: str = "",
        side: str = "BUY",
        qty: int = 0,
        pnl: float = 0.0,
        tags: list[str] | None = None,
        rating: int | None = None,
        lesson: str = "",
    ) -> JournalEntry:
        if not note.strip():
            raise ValueError("note is required")
        if rating is not None and not (1 <= rating <= 5):
            raise ValueError("rating must be between 1 and 5")
        entry = JournalEntry(
            entry_id=secrets.token_hex(6),
            user_id=user_id,
            trade_id=trade_id,
            note=note.strip(),
            symbol=symbol,
            side=side.upper(),
            qty=qty,
            pnl=float(pnl),
            tags=tags or [],
            rating=rating,
            lesson=lesson,
            created_at=datetime.now(),
        )
        self._store.append(user_id, asdict(entry))
        return entry

    def list_entries(self, user_id: str) -> list[JournalEntry]:
        return [_from_dict(e) for e in self._store.load(user_id)]

    def delete_entry(self, user_id: str, entry_id: str) -> bool:
        return self._store.delete(user_id, entry_id)

    def journal_entry(self, user_id: str, trade_id: str, note: str) -> None:
        self.add_entry(user_id, trade_id, note)

    def metrics(self, trades: list[Trade]) -> dict:
        if not trades:
            return {
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "profit_factor": None,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
            }
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl <= 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        return {
            "total_trades": len(trades),
            "win_rate_pct": 100.0 * len(wins) / len(trades),
            "profit_factor": gross_win / gross_loss if gross_loss > 0 else None,
            "total_pnl": sum(t.pnl for t in trades),
            "avg_win": gross_win / len(wins) if wins else 0.0,
            "avg_loss": gross_loss / len(losses) if losses else 0.0,
        }

    def equity_curve(self, trades: list[Trade]) -> pd.Series:
        if not trades:
            return pd.Series(dtype=float)
        index = pd.DatetimeIndex([t.timestamp for t in trades])
        return pd.Series(
            [sum(t.pnl for t in trades[: i + 1]) for i in range(len(trades))],
            index=index,
            name="cumulative_pnl",
        )


def _from_dict(data: dict) -> JournalEntry:
    for key in ("created_at",):
        if data.get(key):
            data[key] = datetime.fromisoformat(str(data[key]))
    data["side"] = data.get("side", "BUY")
    return JournalEntry(**data)
