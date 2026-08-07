from __future__ import annotations

import math
from datetime import date, datetime
from typing import Literal

import pandas as pd
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from modules.backtest_engine import EventDrivenEngine
from modules.shared.contracts import (
    CostModel,
    DataBundle,
    Strategy,
    StrategyConfig,
    SymbolInfo,
)

router = APIRouter(prefix="/api")

EXCHANGE_BY_MARKET = {"IN": "NSE", "US": "US", "CRYPTO": "BINANCE"}
CURRENCY_BY_MARKET = {"IN": "INR", "US": "USD", "CRYPTO": "USDT"}
INSTRUMENT_BY_MARKET = {"IN": "stock", "US": "stock", "CRYPTO": "crypto"}


class BacktestRequest(BaseModel):
    market: Literal["IN", "US", "CRYPTO"]
    symbol: str
    interval: str = "1d"
    start: date
    end: date
    strategy_id: str = "adhoc"
    strategy_version: str = "1.0"
    code: str
    params: dict = Field(default_factory=dict)
    initial_capital: float = 100000.0
    position_sizing: Literal["pct", "fixed"] = "pct"
    position_size: float = 10.0
    costs: dict = Field(default_factory=dict)


@router.post("/backtest")
def run_backtest(req: BacktestRequest) -> dict:
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
        id=req.strategy_id,
        version=req.strategy_version,
        author_user_id="api",
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
    costs = CostModel(**cost_kwargs)

    result = EventDrivenEngine().run(strategy, bundle, costs)
    return serialize_result(result)


def serialize_result(result) -> dict:
    m = result.metrics
    pf = m.profit_factor if math.isfinite(m.profit_factor) else None
    return {
        "strategy_id": result.strategy_id,
        "symbol": result.symbol,
        "interval": result.interval,
        "start": result.start.isoformat(),
        "end": result.end.isoformat(),
        "run_hash": result.run_hash,
        "data_version": result.data_version,
        "equity_curve": [
            {"date": ts.isoformat(), "equity": round(float(equity), 2)}
            for ts, equity in result.equity_curve.items()
        ],
        "trades": [
            {
                "order_id": t.order_id,
                "symbol": t.symbol,
                "side": t.side,
                "qty": t.qty,
                "price": round(float(t.price), 4),
                "fees": round(float(t.fees), 2),
                "pnl": round(float(t.pnl), 2),
                "timestamp": t.timestamp.isoformat(),
            }
            for t in result.trades
        ],
        "metrics": {
            "total_return_pct": round(m.total_return_pct, 4),
            "cagr_pct": round(m.cagr_pct, 4),
            "sharpe": round(m.sharpe, 4),
            "sortino": round(m.sortino, 4),
            "max_drawdown_pct": round(m.max_drawdown_pct, 4),
            "win_rate_pct": round(m.win_rate_pct, 4),
            "profit_factor": round(pf, 4) if pf is not None else None,
            "total_trades": m.total_trades,
            "avg_trade_return_pct": round(m.avg_trade_return_pct, 4),
            "calmar": round(m.calmar, 4),
        },
    }
