from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from modules.shared.contracts import User

router = APIRouter(prefix="/api/journal")


class EntryRequest(BaseModel):
    trade_id: str
    note: str
    symbol: str = ""
    side: str = "BUY"
    qty: int = 0
    pnl: float = 0.0
    tags: list[str] = Field(default_factory=list)
    rating: int | None = None
    lesson: str = ""


@router.post("/entry")
def add_entry(
    req: EntryRequest, user: User = Depends(deps.current_user)
) -> dict:
    try:
        entry = deps.journal_service().add_entry(
            user_id=user.id,
            trade_id=req.trade_id,
            note=req.note,
            symbol=req.symbol,
            side=req.side,
            qty=req.qty,
            pnl=req.pnl,
            tags=req.tags,
            rating=req.rating,
            lesson=req.lesson,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return asdict(entry)


@router.get("")
def list_entries(user: User = Depends(deps.current_user)) -> list[dict]:
    return [asdict(e) for e in deps.journal_service().list_entries(user.id)]


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: str, user: User = Depends(deps.current_user)
) -> dict:
    deleted = deps.journal_service().delete_entry(user.id, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="entry not found")
    return {"deleted": True}


@router.post("/review")
def review_journal(
    user: User = Depends(deps.require_plan("pro"))
) -> dict:
    entries = deps.journal_service().list_entries(user.id)
    text = deps.assistant_service().review_journal(
        user.id, [asdict(e) for e in entries]
    )
    return {"text": text, "entries": len(entries)}
