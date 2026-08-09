from __future__ import annotations

import threading
import uuid
from collections import deque
from datetime import datetime
from typing import Callable, Iterable

from modules.paper_trading.store import AccountStore, Ledger
from modules.shared.contracts import Account, Order, OrderStatus, Position, Trade

DEFAULT_CAPITAL = 100000.0


def replay_trades(
    store: AccountStore, user_id: str, fills: Iterable[tuple[str, str, int, float]]
) -> list[Trade]:
    """Replay historical fills into the paper ledger as MARKET orders.

    Each fill is ``(symbol, side, qty, price)``. Orders are placed in sequence,
    priced at the given historical price, so balance/position rules still apply.
    """
    queue: dict[str, deque] = {}

    def pricer(symbol: str) -> float:
        try:
            return queue[symbol].popleft()
        except (KeyError, IndexError):
            raise RuntimeError(f"no replay price for {symbol}")

    svc = PaperTraderService(store=store, pricer=pricer)
    before = len(svc.history(user_id))
    for symbol, side, qty, price in fills:
        queue.setdefault(symbol, deque()).append(price)
        order = svc.place_order(user_id, symbol, side, int(qty), "MARKET")
        if order.status != "FILLED":
            raise ValueError(f"replay order not filled: {order.status}")
    return svc.history(user_id)[before:]


class PaperTraderService:
    def __init__(
        self,
        store: AccountStore,
        pricer: Callable[[str], float] | None = None,
    ):
        self._store = store
        self._pricer = pricer
        self._lock = threading.RLock()

    def _price(self, symbol: str) -> float:
        if self._pricer is None:
            raise RuntimeError("no price source configured")
        return float(self._pricer(symbol))

    def place_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        qty: int,
        order_type: str = "MARKET",
        price: float | None = None,
        stop_price: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        strategy_id: str | None = None,
    ) -> Order:
        if qty <= 0:
            return self._reject(user_id, symbol, side, qty, order_type, "qty must be positive")
        side = side.upper()
        order_type = order_type.upper()
        with self._lock:
            ledger = self._store.get(user_id)
            order = Order(
                id=uuid.uuid4().hex[:12],
                user_id=user_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                qty=qty,
                price=price,
                stop_price=stop_price,
                sl=sl,
                tp=tp,
                status="OPEN",
                created_at=datetime.utcnow(),
            )
            order = self._try_fill(ledger, order)
            if order.status == "FILLED" and order.order_type == "BRACKET":
                self._attach_protective(ledger, order)
            ledger.orders.append(order)
            self._store.save(user_id)
            return order

    def _try_fill(self, ledger: Ledger, order: Order) -> Order:
        ot = order.order_type
        if ot == "MARKET":
            return self._execute(ledger, order, self._price(order.symbol))
        if ot == "LIMIT" and order.price is not None:
            quote = self._price(order.symbol)
            marketable = (order.side == "BUY" and order.price >= quote) or (
                order.side == "SELL" and order.price <= quote
            )
            if marketable:
                return self._execute(ledger, order, order.price)
            return order
        if ot in ("SL", "STOP", "SL-M"):
            trigger = order.price if order.price is not None else order.stop_price
            if trigger is None:
                return order
            quote = self._price(order.symbol)
            triggered = (order.side == "BUY" and quote >= trigger) or (
                order.side == "SELL" and quote <= trigger
            )
            if triggered:
                return self._execute(ledger, order, quote)
            return order
        if ot == "STOP_LIMIT":
            trigger = order.stop_price if order.stop_price is not None else order.price
            limit = order.price
            if trigger is None or limit is None:
                return order
            quote = self._price(order.symbol)
            triggered = (order.side == "BUY" and quote >= trigger) or (
                order.side == "SELL" and quote <= trigger
            )
            if triggered:
                marketable = (order.side == "BUY" and limit >= quote) or (
                    order.side == "SELL" and limit <= quote
                )
                return self._execute(ledger, order, quote if marketable else limit)
            return order
        if ot == "BRACKET":
            if order.price is not None:
                quote = self._price(order.symbol)
                marketable = (order.side == "BUY" and order.price >= quote) or (
                    order.side == "SELL" and order.price <= quote
                )
                if marketable:
                    return self._execute(ledger, order, order.price)
                return order
            return self._execute(ledger, order, self._price(order.symbol))
        return order

    def _attach_protective(self, ledger: Ledger, order: Order) -> None:
        pos = ledger.positions.get(order.symbol)
        if pos is None:
            return
        sl = order.sl if order.sl is not None else pos.sl
        tp = order.tp if order.tp is not None else pos.tp
        if sl is None and tp is None:
            return
        ledger.positions[order.symbol] = Position(
            symbol=pos.symbol,
            qty=pos.qty,
            avg_price=pos.avg_price,
            ltp=pos.ltp,
            unrealized_pnl=pos.unrealized_pnl,
            sl=sl,
            tp=tp,
        )

    def set_levels(
        self,
        user_id: str,
        symbol: str,
        sl: float | None = None,
        tp: float | None = None,
    ) -> Position | None:
        """Update the SL/TP levels on an open position. Returns None if no position."""
        with self._lock:
            ledger = self._store.get(user_id)
            pos = ledger.positions.get(symbol)
            if pos is None:
                return None
            ltp = self._price(symbol) if self._pricer else pos.avg_price
            updated = Position(
                symbol=pos.symbol,
                qty=pos.qty,
                avg_price=pos.avg_price,
                ltp=ltp,
                unrealized_pnl=(ltp - pos.avg_price) * pos.qty,
                sl=sl,
                tp=tp,
            )
            ledger.positions[symbol] = updated
            self._store.save(user_id)
            return updated

    def check_exits(
        self, user_id: str, quotes: dict[str, float]
    ) -> list[Order]:
        """Close open positions whose protective SL/TP level has been hit.

        ``quotes`` maps symbol -> current price. Returns the exit orders that
        filled. SL/TP are absolute price levels stored on the position.
        """
        with self._lock:
            ledger = self._store.get(user_id)
            exits: list[Order] = []
            for symbol, quote in quotes.items():
                pos = ledger.positions.get(symbol)
                if pos is None or (pos.sl is None and pos.tp is None):
                    continue
                q = float(quote)
                long = pos.qty > 0
                hit: float | None = None
                if long:
                    if pos.sl is not None and q <= pos.sl:
                        hit = pos.sl
                    elif pos.tp is not None and q >= pos.tp:
                        hit = pos.tp
                else:
                    if pos.sl is not None and q >= pos.sl:
                        hit = pos.sl
                    elif pos.tp is not None and q <= pos.tp:
                        hit = pos.tp
                if hit is None:
                    continue
                order = Order(
                    id=uuid.uuid4().hex[:12],
                    user_id=user_id,
                    symbol=symbol,
                    side="SELL" if long else "BUY",
                    order_type="MARKET",
                    qty=abs(pos.qty),
                    status="OPEN",
                    created_at=datetime.utcnow(),
                )
                order = self._execute(ledger, order, q)
                if order.status == "FILLED":
                    ledger.orders.append(order)
                    exits.append(order)
            if exits:
                self._store.save(user_id)
            return exits

    def _execute(self, ledger: Ledger, order: Order, fill: float) -> Order:
        notional = fill * order.qty
        if order.side == "BUY":
            if notional > ledger.balance:
                return self._mark(ledger, order, "REJECTED", "insufficient funds")
            ledger.balance -= notional
            pos = ledger.positions.get(order.symbol)
            if pos is None:
                ledger.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=order.qty,
                    avg_price=fill,
                    sl=order.sl,
                    tp=order.tp,
                )
            else:
                new_qty = pos.qty + order.qty
                new_avg = (pos.avg_price * pos.qty + fill * order.qty) / new_qty
                ledger.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=new_qty,
                    avg_price=new_avg,
                    sl=order.sl if order.sl is not None else pos.sl,
                    tp=order.tp if order.tp is not None else pos.tp,
                )
        else:
            pos = ledger.positions.get(order.symbol)
            if pos is None or pos.qty < order.qty:
                return self._mark(ledger, order, "REJECTED", "insufficient position")
            pnl = (fill - pos.avg_price) * order.qty
            ledger.balance += notional
            remaining = pos.qty - order.qty
            if remaining > 0:
                ledger.positions[order.symbol] = Position(
                    symbol=order.symbol, qty=remaining, avg_price=pos.avg_price
                )
            else:
                del ledger.positions[order.symbol]
            ledger.trades.append(
                Trade(
                    order_id=order.id,
                    symbol=order.symbol,
                    side=order.side,
                    qty=order.qty,
                    price=fill,
                    fees=0.0,
                    pnl=pnl,
                    timestamp=datetime.utcnow(),
                )
            )
        return self._mark(ledger, order, "FILLED", None, fill)

    @staticmethod
    def _mark(
        ledger: Ledger,
        order: Order,
        status: OrderStatus,
        reject_reason: str | None = None,
        fill: float | None = None,
    ) -> Order:
        from dataclasses import replace

        filled_at = datetime.utcnow() if status == "FILLED" else None
        return replace(
            order,
            status=status,
            filled_price=fill,
            filled_at=filled_at,
            sl=None if status == "FILLED" else order.sl,
            tp=None if status == "FILLED" else order.tp,
        )

    def _reject(
        self, user_id: str, symbol: str, side: str, qty: int, order_type: str, reason: str
    ) -> Order:
        return Order(
            id=uuid.uuid4().hex[:12],
            user_id=user_id,
            symbol=symbol,
            side=side.upper(),
            order_type=order_type.upper(),
            qty=qty,
            status="REJECTED",
            created_at=datetime.utcnow(),
        )

    def positions(self, user_id: str) -> list[Position]:
        with self._lock:
            ledger = self._store.get(user_id)
            out = []
            for symbol, pos in ledger.positions.items():
                ltp = self._price(symbol) if self._pricer else pos.avg_price
                unrealized = (ltp - pos.avg_price) * pos.qty
                out.append(
                    Position(
                        symbol=symbol,
                        qty=pos.qty,
                        avg_price=pos.avg_price,
                        ltp=ltp,
                        unrealized_pnl=unrealized,
                        sl=pos.sl,
                        tp=pos.tp,
                    )
                )
            return out

    def history(self, user_id: str) -> list[Trade]:
        with self._lock:
            return list(self._store.get(user_id).trades)

    def reset_account(self, user_id: str, capital: float = DEFAULT_CAPITAL) -> Account:
        with self._lock:
            self._store._ledgers[user_id] = Ledger(user_id=user_id, balance=capital)
            self._store.save(user_id)
            return self.account(user_id)

    def account(self, user_id: str) -> Account:
        with self._lock:
            ledger = self._store.get(user_id)
            positions = self.positions(user_id)
            cost_basis = sum(p.avg_price * p.qty for p in positions)
            unrealized = sum(p.unrealized_pnl for p in positions)
            equity = ledger.balance + cost_basis + unrealized
            return Account(user_id=user_id, balance=ledger.balance, equity=equity, positions=positions)

    def parity_score(self, user_id: str, strategy_id: str) -> float:
        with self._lock:
            trades = [t for t in self._store.get(user_id).trades]
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t.pnl > 0)
        return wins / len(trades)
