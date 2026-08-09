from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user, watchlist_store
from modules.shared.contracts import User

router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])


@router.get("")
def get_watchlists(user: User = Depends(current_user)):
    store = watchlist_store()
    return {"user_id": user.id, "lists": store.list(user.id)}


@router.post("/add")
def add_symbol(body: dict, user: User = Depends(current_user)):
    market = body.get("market", "").upper()
    symbol = body.get("symbol", "").strip().upper()
    if not market or not symbol:
        raise HTTPException(status_code=422, detail="market and symbol required")
    store = watchlist_store()
    return {"user_id": user.id, "lists": store.add(user.id, market, symbol)}


@router.delete("/remove")
def remove_symbol(body: dict, user: User = Depends(current_user)):
    market = body.get("market", "").upper()
    symbol = body.get("symbol", "").strip().upper()
    if not market or not symbol:
        raise HTTPException(status_code=422, detail="market and symbol required")
    store = watchlist_store()
    return {"user_id": user.id, "lists": store.remove(user.id, market, symbol)}
