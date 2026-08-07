from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import pandas as pd

Market = Literal["IN", "US", "CRYPTO"]
Interval = Literal["1d", "1h", "1m"]
Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "SL", "SL-M"]
OrderStatus = Literal["OPEN", "FILLED", "CANCELLED", "REJECTED"]
Plan = Literal["free", "pro"]


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    market: Market
    exchange: str
    name: str
    currency: str
    instrument_type: str
    isin: str | None = None


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    bid: float | None = None
    ask: float | None = None
    volume: float | None = None
    timestamp: datetime | None = None


@dataclass(frozen=True)
class DataBundle:
    symbol: SymbolInfo
    interval: Interval
    df: pd.DataFrame
    source: str
    data_version: str


@dataclass(frozen=True)
class CostModel:
    brokerage: float = 0.0
    brokerage_pct: float = 0.0
    stt_pct: float = 0.0
    exchange_charges_pct: float = 0.0
    sebi_fees_pct: float = 0.0
    gst_pct: float = 0.0
    slippage_pct: float = 0.0
    stamp_duty_pct: float = 0.0


@dataclass(frozen=True)
class StrategyConfig:
    initial_capital: float = 100000.0
    position_sizing: Literal["pct", "fixed"] = "pct"
    position_size: float = 10.0
    max_positions: int = 1
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None


@dataclass(frozen=True)
class Strategy:
    id: str
    version: str
    author_user_id: str
    code: str
    params: dict = field(default_factory=dict)
    config: StrategyConfig = field(default_factory=StrategyConfig)
    data_version: str = ""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Metrics:
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_trade_return_pct: float = 0.0
    calmar: float = 0.0


@dataclass(frozen=True)
class Trade:
    order_id: str
    symbol: str
    side: Side
    qty: int
    price: float
    fees: float
    pnl: float
    timestamp: datetime
    strategy_id: str | None = None


@dataclass(frozen=True)
class BacktestResult:
    strategy_id: str
    symbol: str
    interval: Interval
    start: datetime
    end: datetime
    equity_curve: pd.Series
    trades: list[Trade]
    metrics: Metrics
    run_hash: str
    data_version: str


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    symbol: str
    side: Side
    order_type: OrderType
    qty: int
    price: float | None = None
    sl: float | None = None
    tp: float | None = None
    status: OrderStatus = "OPEN"
    filled_price: float | None = None
    filled_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: int
    avg_price: float
    ltp: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass(frozen=True)
class Account:
    user_id: str
    balance: float
    equity: float
    positions: list[Position] = field(default_factory=list)


@dataclass(frozen=True)
class User:
    id: str
    email: str
    plan: Plan = "free"


@dataclass(frozen=True)
class Session:
    user_id: str
    token: str
    expires_at: datetime | None = None


@dataclass(frozen=True)
class AssistantReply:
    text: str
    action_taken: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    needs_confirmation: bool = False
    audio_url: str | None = None


@dataclass(frozen=True)
class JournalEntry:
    entry_id: str
    user_id: str
    trade_id: str
    note: str
    symbol: str = ""
    side: Side = "BUY"
    qty: int = 0
    pnl: float = 0.0
    tags: list[str] = field(default_factory=list)
    rating: int | None = None
    lesson: str = ""
    created_at: datetime | None = None


@dataclass(frozen=True)
class ScreenerRow:
    symbol: str
    last_close: float
    change_1d_pct: float | None = None
    change_5d_pct: float | None = None
    change_1m_pct: float | None = None
    change_3m_pct: float | None = None
    avg_volume_20: float | None = None
    above_sma_50: bool | None = None
    above_sma_200: bool | None = None
