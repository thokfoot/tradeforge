from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from modules.screener import new_saved_scan
from modules.shared.contracts import User

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


class SaveScanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    market: Literal["IN", "US", "CRYPTO"]
    filters: dict = {}
    limit: int = 50


@router.post("/scans/save")
def save_scan(
    req: SaveScanRequest, user: User = Depends(deps.current_user)
) -> dict:
    scan = new_saved_scan(
        user_id=user.id,
        name=req.name,
        market=req.market,
        filters=req.filters,
        limit=req.limit,
    )
    return asdict(deps.scan_store().add(scan))


@router.get("/scans")
def list_scans(user: User = Depends(deps.current_user)) -> list[dict]:
    return [asdict(s) for s in deps.scan_store().list(user.id)]


@router.delete("/scans/{scan_id}")
def delete_scan(
    scan_id: str, user: User = Depends(deps.current_user)
) -> dict:
    deleted = deps.scan_store().delete(user.id, scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="scan not found")
    return {"deleted": True}


@router.post("/scans/{scan_id}/run")
def run_saved_scan(
    scan_id: str, user: User = Depends(deps.current_user)
) -> dict:
    scan = deps.scan_store().get(user.id, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan not found")
    provider = deps.provider_for(scan.market)
    symbols = [s.symbol for s in provider.get_symbols()]
    rows = deps.screener_service(scan.market).scan(
        symbols, scan.filters, scan.limit
    )
    return {
        "scan_id": scan.id,
        "name": scan.name,
        "market": scan.market,
        "scanned": min(len(symbols), scan.limit),
        "count": len(rows),
        "results": [asdict(r) for r in rows],
    }
