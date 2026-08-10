from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.api.market import normalize_in_symbol
from modules.backtest_engine import EventDrivenEngine
from modules.paper_trading import replay_trades
from modules.shared.contracts import (
    CostModel,
    DataBundle,
    Strategy,
    StrategyConfig,
    SymbolInfo,
    User,
)

router = APIRouter(prefix="/api/paper")

EXCHANGE_BY_MARKET = {"IN": "NSE", "US": "US", "CRYPTO": "BINANCE"}
CURRENCY_BY_MARKET = {"IN": "INR", "US": "USD", "CRYPTO": "USDT"}
INSTRUMENT_BY_MARKET = {"IN": "stock", "US": "stock", "CRYPTO": "crypto"}


class OrderRequest(BaseModel):
    market: Literal["IN", "US", "CRYPTO"] = "IN"
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int = Field(..., gt=0)
    order_type: Literal[
        "MARKET", "LIMIT", "SL", "SL-M", "STOP", "STOP_LIMIT", "BRACKET"
    ] = "MARKET"
    price: float | None = None
    stop_price: float | None = None
    sl: float | None = None
    tp: float | None = None
    strategy_id: str | None = None


class ExitsRequest(BaseModel):
    market: Literal["IN", "US", "CRYPTO"] = "IN"
    prices: dict[str, float] = Field(default_factory=dict)


@router.post("/order")
def place_order(
    req: OrderRequest, user: User = Depends(deps.current_user)
) -> dict:
    service = deps.paper_service(req.market)
    symbol = normalize_in_symbol(req.symbol) if req.market == "IN" else req.symbol
    order = service.place_order(
        user_id=user.id,
        symbol=symbol,
        side=req.side,
        qty=req.qty,
        order_type=req.order_type,
        price=req.price,
        stop_price=req.stop_price,
        sl=req.sl,
        tp=req.tp,
        strategy_id=req.strategy_id,
    )
    return asdict(order)


class LevelsRequest(BaseModel):
    market: Literal["IN", "US", "CRYPTO"] = "IN"
    symbol: str
    sl: float | None = None
    tp: float | None = None


@router.post("/position/levels")
def set_levels(
    req: LevelsRequest, user: User = Depends(deps.current_user)
) -> dict:
    pos = deps.paper_service(req.market).set_levels(
        user.id,
        normalize_in_symbol(req.symbol) if req.market == "IN" else req.symbol,
        req.sl,
        req.tp,
    )
    if pos is None:
        raise HTTPException(status_code=404, detail="no open position")
    return asdict(pos)


@router.post("/check-exits")
def check_exits(
    req: ExitsRequest, user: User = Depends(deps.current_user)
) -> dict:
    orders = deps.paper_service(req.market).check_exits(user.id, req.prices)
    return {"orders": [asdict(o) for o in orders], "count": len(orders)}


@router.get("/account")
def get_account(
    market: str = "IN", user: User = Depends(deps.current_user)
) -> dict:
    return asdict(deps.paper_service(market).account(user.id))


@router.get("/positions")
def get_positions(
    market: str = "IN", user: User = Depends(deps.current_user)
) -> list[dict]:
    return [asdict(p) for p in deps.paper_service(market).positions(user.id)]


@router.get("/history")
def get_history(user: User = Depends(deps.current_user)) -> list[dict]:
    return [asdict(t) for t in deps.paper_service().history(user.id)]


@router.post("/reset")
def reset_account(
    market: str = "IN",
    amount: float | None = None,
    user: User = Depends(deps.current_user),
) -> dict:
    capital = amount if amount is not None else deps.DEFAULT_CAPITAL
    return asdict(deps.paper_service(market).reset_account(user.id, capital))


class ReplayRequest(BaseModel):
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


def _run_replay(user: User, req: ReplayRequest) -> dict:
    provider = deps.provider_for(req.market)
    symbol = normalize_in_symbol(req.symbol) if req.market == "IN" else req.symbol
    try:
        df = provider.fetch_ohlcv(
            symbol, req.interval, pd.Timestamp(req.start), pd.Timestamp(req.end)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if df.empty:
        raise HTTPException(status_code=404, detail=f"no data for {req.symbol}")

    symbol_info = SymbolInfo(
        symbol=symbol,
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
        author_user_id=user.id,
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
    round_trips = 0
    for t in result.trades:
        if t.entry_timestamp is not None:
            round_trips += 1
        fills.append((result.symbol, t.side, int(t.qty), float(t.price)))

    service = deps.paper_service(req.market)
    service.reset_account(user.id, req.initial_capital)
    trades = replay_trades(deps.paper_store(), user.id, fills)
    account = service.account(user.id)
    return {
        "user_id": user.id,
        "market": req.market,
        "symbol": result.symbol,
        "interval": result.interval,
        "fills": len(fills),
        "round_trips": round_trips,
        "replayed_trades": [asdict(t) for t in trades],
        "account": asdict(account),
        "metrics": {
            "total_return_pct": round(result.metrics.total_return_pct, 4),
            "total_trades": result.metrics.total_trades,
            "win_rate_pct": round(result.metrics.win_rate_pct, 4),
        },
    }


@router.post("/replay")
def replay(
    req: ReplayRequest, user: User = Depends(deps.current_user)
) -> dict:
    return _run_replay(user, req)


class PaperTradingStartRequest(ReplayRequest):
    strategy_id: str = "adhoc"


start_router = APIRouter(prefix="/api/paper-trading")


@start_router.post("/start")
def start_paper_trading(
    req: PaperTradingStartRequest, user: User = Depends(deps.current_user)
) -> dict:
    result = _run_replay(user, req)
    result["status"] = "started"
    result["strategy_id"] = req.strategy_id
    result["message"] = "paper trading started"
    return result
