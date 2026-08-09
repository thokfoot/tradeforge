from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from modules.shared.contracts import Account, Order, Position, Trade
from modules.shared.safety import safe_id


@dataclass
class Ledger:
    user_id: str
    balance: float = 100000.0
    positions: dict[str, Position] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)

    def equity(self) -> float:
        pnl = sum(p.unrealized_pnl for p in self.positions.values())
        return self.balance + pnl


class AccountStore:
    def __init__(self, path: Path | None = None):
        self._path = path
        self._ledgers: dict[str, Ledger] = {}
        if path is not None:
            self._load()

    def get(self, user_id: str) -> Ledger:
        if user_id not in self._ledgers:
            self._ledgers[user_id] = Ledger(user_id=user_id)
            self.save(user_id)
        return self._ledgers[user_id]

    def save(self, user_id: str) -> None:
        if self._path is None:
            return
        self._path.mkdir(parents=True, exist_ok=True)
        ledger = self._ledgers[user_id]
        payload = {
            "user_id": ledger.user_id,
            "balance": ledger.balance,
            "positions": [asdict(p) for p in ledger.positions.values()],
            "orders": [_order_to_dict(o) for o in ledger.orders],
            "trades": [asdict(t) for t in ledger.trades],
        }
        file = self._path / f"{safe_id(user_id)}.json"
        file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _load(self) -> None:
        if self._path is None:
            return
        for file in self._path.glob("*.json"):
            payload = json.loads(file.read_text(encoding="utf-8"))
            ledger = Ledger(
                user_id=payload["user_id"],
                balance=payload["balance"],
                positions={
                    p["symbol"]: Position(
                        symbol=p["symbol"],
                        qty=p["qty"],
                        avg_price=p["avg_price"],
                        ltp=p.get("ltp", 0.0),
                        unrealized_pnl=p.get("unrealized_pnl", 0.0),
                        sl=p.get("sl"),
                        tp=p.get("tp"),
                    )
                    for p in payload.get("positions", [])
                },
                orders=[_order_from_dict(o) for o in payload.get("orders", [])],
                trades=[Trade(**t) for t in payload.get("trades", [])],
            )
            self._ledgers[ledger.user_id] = ledger


def _order_to_dict(order: Order) -> dict:
    return asdict(order)


def _order_from_dict(data: dict) -> Order:
    for key in ("created_at", "filled_at"):
        if data.get(key):
            data[key] = datetime.fromisoformat(str(data[key]))
    return Order(**data)
