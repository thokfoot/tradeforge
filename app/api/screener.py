from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.api import deps

router = APIRouter(prefix="/api/screener")


class ScreenerRequest(BaseModel):
    market: Literal["IN", "US", "CRYPTO"]
    filters: dict = {}
    limit: int = 50


@router.post("/scan")
def scan(req: ScreenerRequest) -> dict:
    provider = deps.provider_for(req.market)
    symbols = [s.symbol for s in provider.get_symbols()]
    rows = deps.screener_service(req.market).scan(symbols, req.filters, req.limit)
    return {
        "market": req.market,
        "scanned": min(len(symbols), req.limit),
        "count": len(rows),
        "results": [asdict(r) for r in rows],
    }
