from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Literal

import pandas as pd
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from modules.backtest_engine import EventDrivenEngine
from modules.paper_trading import replay_trades
from modules.shared.contracts import (
    CostModel,
    DataBundle,
    Strategy,
    StrategyConfig,
    SymbolInfo,
)

router = APIRouter(prefix="/api/paper")

EXCHANGE_BY_MARKET = {"IN": "NSE", "US": "US", "CRYPTO": "BINANCE"}
CURRENCY_BY_MARKET = {"IN": "INR", "US": "USD", "CRYPTO": "USDT"}
INSTRUMENT_BY_MARKET = {"IN": "stock", "US": "stock", "CRYPTO": "crypto"}


class OrderRequest(BaseModel):
    user_id: str
    market: Literal["IN", "US", "CRYPTO"] = "IN"
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int = Field(..., gt=0)
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    price: float | None = None
    strategy_id: str | None = None


@router.post("/order")
def place_order(req: OrderRequest) -> dict:
    service = deps.paper_service(req.market)
    order = service.place_order(
        user_id=req.user_id,
        symbol=req.symbol,
        side=req.side,
        qty=req.qty,
        order_type=req.order_type,
        price=req.price,
        strategy_id=req.strategy_id,
    )
    return asdict(order)


@router.get("/account")
def get_account(user_id: str, market: str = "IN") -> dict:
    return asdict(deps.paper_service(market).account(user_id))


@router.get("/positions")
def get_positions(user_id: str, market: str = "IN") -> list[dict]:
    return [asdict(p) for p in deps.paper_service(market).positions(user_id)]


@router.get("/history")
def get_history(user_id: str) -> list[dict]:
    return [asdict(t) for t in deps.paper_service().history(user_id)]


@router.post("/reset")
def reset_account(user_id: str, market: str = "IN") -> dict:
    return asdict(deps.paper_service(market).reset_account(user_id))


class ReplayRequest(BaseModel):
    user_id: str
    market: Literal["IN", "US", "CRYPTO"]
    symbol: str
    interval: str = "1d"
    start: date
    end: date
    code: str
    params: dict = Field(default_factory=dict)
    initial_capital: float = 100000.0
    position_sizing: Literal["pct", "fixed"] = "pct"
    position_size: float = 10.0
    costs: dict = Field(default_factory=dict)


@router.post("/replay")
def replay(req: ReplayRequest) -> dict:
    provider = deps.provider_for(req.market)
    try:
        df = provider.fetch_ohlcv(
            req.symbol, req.interval, pd.Timestamp(req.start), pd.Timestamp(req.end)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if df.empty:
        raise HTTPException(status_code=404, detail=f"no data for {req.symbol}")

    symbol_info = SymbolInfo(
        symbol=req.symbol,
        market=req.market,
        exchange=EXCHANGE_BY_MARKET[req.market],
        name=req.symbol,
        currency=CURRENCY_BY_MARKET[req.market],
        instrument_type=INSTRUMENT_BY_MARKET[req.market],
    )
    bundle = DataBundle(
        symbol=symbol_info,
        interval=req.interval,
        df=df,
        source="api",
        data_version="v1",
    )
    strategy = Strategy(
        id="replay",
        version="1.0",
        author_user_id=req.user_id,
        code=req.code,
        params=req.params,
        config=StrategyConfig(
            initial_capital=req.initial_capital,
            position_sizing=req.position_sizing,
            position_size=req.position_size,
        ),
    )
    cost_kwargs = {
        k: v
        for k, v in req.costs.items()
        if k in CostModel.__dataclass_fields__
    }
    result = EventDrivenEngine().run(strategy, bundle, CostModel(**cost_kwargs))

    fills = []
    for t in result.trades:
        entry_price = t.price - (t.pnl + t.fees) / t.qty
        fills.append((result.symbol, "BUY", int(t.qty), entry_price))
        fills.append((result.symbol, "SELL", int(t.qty), float(t.price)))

    service = deps.paper_service(req.market)
    service.reset_account(req.user_id, req.initial_capital)
    trades = replay_trades(deps.paper_store(), req.user_id, fills)
    account = service.account(req.user_id)
    return {
        "user_id": req.user_id,
        "market": req.market,
        "symbol": result.symbol,
        "interval": result.interval,
        "fills": len(fills),
        "round_trips": len(result.trades),
        "replayed_trades": [asdict(t) for t in trades],
        "account": asdict(account),
        "metrics": {
            "total_return_pct": round(result.metrics.total_return_pct, 4),
            "total_trades": result.metrics.total_trades,
            "win_rate_pct": round(result.metrics.win_rate_pct, 4),
        },
    }
