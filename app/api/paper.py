from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api import deps

router = APIRouter(prefix="/api/paper")


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
